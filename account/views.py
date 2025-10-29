from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from account.models.users import UserModel
from account.serializers import UpdateUserBVNSerializer, UpdateUserNINSerializer, UpdateUserProfileSerializer, UserProfileSerializer
from core.helpers.response import error_response, success_response, validation_error_response
from providers.helpers.embedly import EmbedlyClient
from wallet.models import Wallet
from account.services.sync_embedly import EmbedlySyncService
 

class UserProfileView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve the authenticated user's profile.
        """
        user = request.user
        serializer = UserProfileSerializer(user)
  
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Update the authenticated user's profile.
        """
        user = request.user
        serializer = UpdateUserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class UpdateBVNView(APIView):
    """
    View to update a user's BVN (Bank Verification Number) and create a virtual wallet.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = UpdateUserBVNSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return validation_error_response(serializer.errors)

        embedly_client = EmbedlyClient()

        # Check if BVN is already verified
        if user.has_bvn:
            return error_response("BVN has already been verified for this account.")

        # Check if BVN is used by another account
        if UserModel.objects.filter(bvn=serializer.validated_data["bvn"]).exists():
            return error_response(
                "BVN has already been used for another account. Please log in to your other account."
            )

        # Verify BVN with Embedly
        res = embedly_client.upgrade_kyc(
            customer_id=user.embedly_customer_id,
            bvn=serializer.validated_data["bvn"]
        )

        if not res.get("success"):
            return error_response(res.get("data", {}).get("message", "BVN verification failed."))

        data = res.get("data", {})
        if not (data.get("successful") and data.get("kycCompleted")):
            return error_response("BVN validation service is currently not available.")

        response_status = data.get("response", {}).get("status", {}).get("status")
        if response_status != "verified":
            if data.get("response_code") == "01":
                return error_response("Invalid BVN provided.")
            return error_response("BVN validation service is currently not available.")

        # Update user BVN data
        bvn_data = data["response"]["bvn"]
        self._update_user_bvn_data(user, bvn_data)
        serializer.save()

        # Upgrade account tier based on verification level
        if user.has_bvn and user.has_nin:
            # Both verified = Tier 2
            user.account_tier = "Tier 2"
            tier_message = "Congratulations! You now have Tier 2 access with both BVN and NIN verified! Daily limit: ₦100K, Cumulative: ₦500K"
        elif user.has_bvn:
            # Only BVN verified = Tier 1
            user.account_tier = "Tier 1"
            tier_message = "BVN verified successfully! You now have Tier 1 access. Daily limit: ₦50K. Add NIN to upgrade to Tier 2 for higher limits."

        user.save(update_fields=["account_tier"])

        # Create wallet if user doesn't have one yet
        if not user.has_virtual_wallet and user.embedly_customer_id:
            return self._create_wallet_for_user(user, embedly_client)

        return success_response(tier_message)

    def _update_user_bvn_data(self, user, bvn_data):
        """Update user's BVN-related fields after successful verification."""
        user.bvn_first_name = bvn_data.get("firstname")
        user.bvn_last_name = bvn_data.get("lastname")
        user.bvn_gender = bvn_data.get("gender")
        user.bvn_phone = bvn_data.get("phone")
        user.image = bvn_data.get("photo")
        user.bvn_dob = bvn_data.get("birthdate")
        user.bvn_marital_status = bvn_data.get("marital_status")
        user.bvn_nationality = bvn_data.get("nationality")
        user.bvn_residential_address = bvn_data.get("residential_address")
        user.bvn_state_of_residence = bvn_data.get("state_of_residence")
        user.bvn_watch_listed = bvn_data.get("watch_listed")
        user.bvn_enrollment_bank = bvn_data.get("enrollment_bank")
        user.has_bvn = True
        user.save(update_fields=[
            "bvn_first_name", "bvn_last_name", "bvn_gender", "bvn_phone", "image",
            "bvn_dob", "bvn_marital_status", "bvn_nationality", "bvn_residential_address",
            "bvn_state_of_residence", "bvn_watch_listed", "bvn_enrollment_bank", "has_bvn"
        ])

    def _create_wallet_for_user(self, user, embedly_client):
        """Create a virtual wallet for a user if they don’t already have one."""
        wallet_res = embedly_client.create_wallet(
            customer_id=user.embedly_customer_id,
            name=f"{user.first_name} {user.last_name}",
            phone=user.phone
        )

        print(wallet_res)

        if not wallet_res.get("success"):
            return error_response("Failed to create virtual wallet.")

        data = wallet_res["data"]["virtualAccount"]
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.account_name = f"{user.first_name} {user.last_name}"
        wallet.account_number = data.get("accountNumber")
        wallet.bank = data.get("bankName")
        wallet.bank_code = data.get("bankCode")
        wallet.embedly_wallet_id = wallet_res["data"]["id"]
        wallet.save()

        user.embedly_wallet_id = wallet_res["data"]["id"]
        user.has_virtual_wallet = True
        user.save(update_fields=["embedly_wallet_id", "has_virtual_wallet"])

        return success_response("BVN Verified successfully.")


class UpdateNINView(APIView):
    """
    View to update a user's NIN (National Identification Number) and create a virtual wallet.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print(f"NIN Update Request Data: {request.data}")  # Debug log
        serializer = UpdateUserNINSerializer(data=request.data)

        if not serializer.is_valid():
            print(f"NIN Validation Errors: {serializer.errors}")  # Debug log
            return validation_error_response(serializer.errors)

        embedly_client = EmbedlyClient()

        # Check if NIN is already verified
        if user.has_nin:
            return error_response("NIN has already been verified for this account.")

        # Check if NIN is used by another account
        if UserModel.objects.filter(nin=serializer.validated_data["nin"]).exists():
            return error_response(
                "NIN has already been used for another account. Please log in to your other account."
            )

        # Verify NIN with Embedly
        res = embedly_client.upgrade_kyc_nin(
            customer_id=user.embedly_customer_id,
            nin=serializer.validated_data["nin"],
            firstname=serializer.validated_data["firstname"],
            lastname=serializer.validated_data["lastname"],
            dob=serializer.validated_data["dob"]
        )

        # Handle Embedly response
        if not res.get("success"):
            # Check if error is because user already has KYC (from BVN)
            error_code = res.get("code")
            error_message = res.get("message", "")

            if error_code == "-904" or "already completed this level of KYC" in error_message:
                # User already has BVN verified, so Embedly KYC level is met
                # We still want to store the NIN for our Tier 3 upgrade
                print(f"Embedly KYC already completed (user has BVN), storing NIN for Tier 3 upgrade")

                # Store NIN without Embedly verification data
                user.nin = serializer.validated_data["nin"]
                user.has_nin = True
                user.save(update_fields=["nin", "has_nin"])

                # Upgrade to Tier 2 since user now has both BVN and NIN
                if user.has_bvn:
                    user.account_tier = "Tier 2"
                    user.save(update_fields=["account_tier"])

                    success_msg = {
                        "message": "Congratulations! You now have Tier 2 access!",
                        "details": "Both BVN and NIN are now verified. You have unlocked higher transaction limits!",
                        "tier": "Tier 2",
                        "daily_limit": "₦100,000",
                        "cumulative_limit": "₦500,000",
                        "wallet_balance_limit": "₦500,000",
                        "benefits": [
                            "All Tier 1 features",
                            "Community groups",
                            "Higher transaction limits"
                        ],
                        "next_steps": "Complete address verification and upload proof of address (utility bill) to upgrade to Tier 3 (Unlimited) - coming soon"
                    }
                    return success_response(success_msg)

                return success_response("NIN added successfully!")
            else:
                return error_response(res.get("message", "NIN verification failed."))

        data = res.get("data", {})
        if not (data.get("successful") and data.get("kycCompleted")):
            return error_response("NIN validation service is currently not available.")

        response_status = data.get("response", {}).get("status", {}).get("status")
        if response_status != "verified":
            if data.get("response_code") == "01":
                return error_response("Invalid NIN provided.")
            return error_response("NIN validation service is currently not available.")

        # Update user NIN data with Embedly verification details
        nin_data = data["response"]["nin"]
        user.nin = serializer.validated_data["nin"]  # Save the NIN to user model
        self._update_user_nin_data(user, nin_data)

        # Upgrade account tier based on verification level
        if user.has_bvn and user.has_nin:
            # Both verified = Tier 2
            user.account_tier = "Tier 2"
            tier_message = "Congratulations! You now have Tier 2 access with both BVN and NIN verified! Daily limit: ₦100K, Cumulative: ₦500K"
        elif user.has_nin:
            # Only NIN verified = Tier 1
            user.account_tier = "Tier 1"
            tier_message = "NIN verified successfully! You now have Tier 1 access. Daily limit: ₦50K. Add BVN to upgrade to Tier 2 for higher limits."

        user.save(update_fields=["account_tier"])

        # Create wallet if user doesn't have one yet
        if not user.has_virtual_wallet and user.embedly_customer_id:
            return self._create_wallet_for_user(user, embedly_client)

        return success_response(tier_message)

    def _update_user_nin_data(self, user, nin_data):
        """Update user's NIN-related fields after successful verification."""
        user.nin_first_name = nin_data.get("firstname")
        user.nin_last_name = nin_data.get("lastname")
        user.nin_gender = nin_data.get("gender")
        user.nin_phone = nin_data.get("phone")
        user.image = nin_data.get("photo")
        user.nin_dob = nin_data.get("birthdate")
        user.nin_marital_status = nin_data.get("marital_status")
        user.nin_nationality = nin_data.get("nationality")
        user.nin_residential_address = nin_data.get("residential_address")
        user.nin_state_of_residence = nin_data.get("state_of_residence")
        user.has_nin = True
        user.save(update_fields=[
            "nin_first_name", "nin_last_name", "nin_gender", "nin_phone", "image",
            "nin_dob", "nin_marital_status", "nin_nationality", "nin_residential_address",
            "nin_state_of_residence", "has_nin"
        ])

    def _create_wallet_for_user(self, user, embedly_client):
        """Create a virtual wallet for a user if they don't already have one."""
        wallet_res = embedly_client.create_wallet(
            customer_id=user.embedly_customer_id,
            name=f"{user.first_name} {user.last_name}",
            phone=user.phone
        )

        print(wallet_res)

        if not wallet_res.get("success"):
            return error_response("Failed to create virtual wallet.")

        data = wallet_res["data"]["virtualAccount"]
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.account_name = f"{user.first_name} {user.last_name}"
        wallet.account_number = data.get("accountNumber")
        wallet.bank = data.get("bankName")
        wallet.bank_code = data.get("bankCode")
        wallet.embedly_wallet_id = wallet_res["data"]["id"]
        wallet.save()

        user.embedly_wallet_id = wallet_res["data"]["id"]
        user.has_virtual_wallet = True
        user.save(update_fields=["embedly_wallet_id", "has_virtual_wallet"])

        return success_response("NIN Verified successfully.")


class VerificationStatusView(APIView):
    """
    View to check user's BVN and NIN verification status.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        response_data = {
            "bvn": {
                "verified": user.has_bvn,
                "bvn_number": user.bvn if user.has_bvn else None,
                "verified_name": f"{user.bvn_first_name} {user.bvn_last_name}" if user.has_bvn else None,
                "dob": user.bvn_dob if user.has_bvn else None,
            },
            "nin": {
                "verified": user.has_nin,
                "nin_number": user.nin if user.has_nin else None,
                "verified_name": f"{user.nin_first_name} {user.nin_last_name}" if user.has_nin else None,
                "dob": user.nin_dob if user.has_nin else None,
            },
            "account_info": {
                "account_tier": user.account_tier,
                "has_virtual_wallet": user.has_virtual_wallet,
                "profile_name": f"{user.first_name} {user.last_name}",
                "profile_dob": user.dob,
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)


class AccountTierInfoView(APIView):
    """
    View to get account tier information, limits, and upgrade options.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Define tier limits (from Embedly KYC requirements)
        tier_limits = {
            "Tier 1": {
                "name": "Tier 1",
                "daily_transaction_limit": 50000,
                "cumulative_transaction_limit": 300000,
                "wallet_balance_limit": 300000,
                "features": ["Basic wallet", "Send money", "Receive money", "Savings"],
                "requirements": ["BVN or NIN verification"],
                "is_current": user.account_tier == "Tier 1",
                "can_upgrade": not (user.has_bvn and user.has_nin)
            },
            "Tier 2": {
                "name": "Tier 2",
                "daily_transaction_limit": 100000,
                "cumulative_transaction_limit": 500000,
                "wallet_balance_limit": 500000,
                "features": ["All Tier 1 features", "Community groups", "Higher limits"],
                "requirements": ["BVN and NIN verification"],
                "is_current": user.account_tier == "Tier 2",
                "can_upgrade": not (user.has_bvn and user.has_nin)
            },
            "Tier 3": {
                "name": "Tier 3 - Premium (Unlimited)",
                "daily_transaction_limit": "Unlimited",
                "cumulative_transaction_limit": "Unlimited",
                "wallet_balance_limit": "Unlimited",
                "features": ["All Tier 2 features", "Unlimited transactions", "Unlimited balance", "Premium support", "Priority processing"],
                "requirements": ["BVN and NIN verification", "Address", "Proof of Address (Utility bill)"],
                "is_current": user.account_tier == "Tier 3",
                "can_upgrade": False,  # Tier 3 is max tier
                "note": "Address and proof of address verification coming soon"
            }
        }

        # Current tier info
        current_tier = tier_limits.get(user.account_tier, tier_limits["Tier 1"])

        # Upgrade options
        upgrade_options = []

        # No verification yet - can add BVN or NIN for Tier 1
        if not user.has_bvn and not user.has_nin:
            upgrade_options.append({
                "type": "BVN",
                "description": "Verify your BVN to unlock Tier 1 (₦50K daily limit)",
                "endpoint": "/api/v1/account/bvn-update"
            })
            upgrade_options.append({
                "type": "NIN",
                "description": "Verify your NIN to unlock Tier 1 (₦50K daily limit)",
                "endpoint": "/api/v1/account/nin-update"
            })

        # Has one verification - can add the other for Tier 2
        elif (user.has_bvn or user.has_nin) and not (user.has_bvn and user.has_nin):
            missing = "NIN" if user.has_bvn else "BVN"
            upgrade_options.append({
                "type": missing,
                "description": f"Add {missing} verification to upgrade to Tier 2 (₦100K daily limit)",
                "endpoint": f"/api/v1/account/{missing.lower()}-update"
            })

        # Has both - can upgrade to Tier 3 with address verification
        elif user.has_bvn and user.has_nin and user.account_tier != "Tier 3":
            upgrade_options.append({
                "type": "Address Verification",
                "description": "Complete address verification and upload proof of address for Tier 3 (Unlimited)",
                "endpoint": "/api/v1/account/address-update",
                "status": "Coming soon"
            })

        response_data = {
            "current_tier": current_tier,
            "all_tiers": tier_limits,
            "verification_status": {
                "has_bvn": user.has_bvn,
                "has_nin": user.has_nin,
                "has_virtual_wallet": user.has_virtual_wallet,
                "bvn_verified_name": f"{user.bvn_first_name} {user.bvn_last_name}" if user.has_bvn else None,
                "nin_verified_name": f"{user.nin_first_name} {user.nin_last_name}" if user.has_nin else None
            },
            "upgrade_options": upgrade_options
        }

        return Response(response_data, status=status.HTTP_200_OK)


class SyncEmbedlyVerificationView(APIView):
    """
    View to manually sync user's verification status from Embedly.
    Useful for fixing discrepancies between Embedly and local database.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Sync the authenticated user's verification status from Embedly.
        """
        user = request.user

        if not user.embedly_customer_id:
            return error_response("No Embedly account associated with this user.")

        # Run the sync
        sync_service = EmbedlySyncService()
        result = sync_service.sync_user_verification(user)

        if not result["success"]:
            return error_response(result.get("message", "Failed to sync verification status."))

        # Prepare response
        if result.get("updated"):
            message = f"Verification status synced successfully! Changes: {', '.join(result['changes'])}"
        else:
            message = "Verification status is already up to date."

        response_data = {
            "message": message,
            "updated": result.get("updated", False),
            "changes": result.get("changes", []),
            "current_status": {
                "account_tier": user.account_tier,
                "has_bvn": user.has_bvn,
                "has_nin": user.has_nin,
                "has_virtual_wallet": user.has_virtual_wallet,
            }
        }

        return success_response(response_data)

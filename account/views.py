from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from account.models.users import UserModel
from account.serializers import UpdateUserBVNSerializer, UpdateUserProfileSerializer, UserProfileSerializer
from core.helpers.response import error_response, success_response, validation_error_response
from providers.helpers.embedly import EmbedlyClient
from wallet.models import Wallet
 

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

        if user.has_bvn:
            if not user.has_virtual_wallet and user.embedly_customer_id:
                return self._create_wallet_for_user(user, embedly_client)
            return error_response("BVN has already been verified for this account.")

        if UserModel.objects.filter(bvn=serializer.validated_data["bvn"]).exists():
            return error_response(
                "BVN has already been used for another account. Please log in to your other account."
            )

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

        bvn_data = data["response"]["bvn"]
        self._update_user_bvn_data(user, bvn_data)
        serializer.save()

        return self._create_wallet_for_user(user, embedly_client)

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

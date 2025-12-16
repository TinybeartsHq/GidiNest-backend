"""
V2 KYC Views - Prembly Integration
Two-step BVN and NIN verification flow for mobile app
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from datetime import datetime
import logging
import uuid

from account.models.users import UserModel
from account.serializers import (
    V2BVNVerifySerializer,
    V2BVNConfirmSerializer,
    V2NINVerifySerializer,
    V2NINConfirmSerializer
)
from providers.helpers.prembly import verify_bvn, verify_nin
from providers.helpers.psb9 import psb9_client
from wallet.models import Wallet

logger = logging.getLogger(__name__)


class V2BVNVerifyView(APIView):
    """
    Step 1: Verify BVN with Prembly
    Returns BVN details for user review without saving to database
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = V2BVNVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "data": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        bvn = serializer.validated_data['bvn']

        # Check if BVN is already verified for this user
        # Allow retry if wallet doesn't exist (wallet creation may have failed previously)
        if user.has_bvn:
            # Check if wallet exists
            try:
                wallet = user.wallet
                # Wallet exists, check if it has 9PSB account number
                if wallet.psb9_account_number:
                    return Response({
                        "success": False,
                        "error": {
                            "code": "KYC_BVN_ALREADY_VERIFIED",
                            "message": "BVN has already been verified and wallet created for this account"
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Wallet exists but no 9PSB account - allow retry
                    logger.info(f"User {user.email} has BVN but no 9PSB account, allowing retry")
            except Wallet.DoesNotExist:
                # No wallet exists - allow retry to create wallet
                logger.info(f"User {user.email} has BVN but no wallet, allowing retry for wallet creation")

        # Check if BVN is used by another account
        # Skip duplicate check in DEBUG mode for testing
        if not settings.DEBUG:
            if UserModel.objects.filter(bvn=bvn).exclude(id=user.id).exists():
                return Response({
                    "success": False,
                    "error": {
                        "code": "KYC_BVN_DUPLICATE",
                        "message": "This BVN has already been used for another account"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # In DEBUG mode, allow duplicate BVNs but log a warning
            if UserModel.objects.filter(bvn=bvn).exclude(id=user.id).exists():
                logger.warning(f"TEST MODE: Allowing duplicate BVN {bvn} for user {user.email}")

        # If user already has BVN verified, use stored data instead of calling Prembly
        if user.has_bvn and user.bvn == bvn:
            logger.info(f"Using stored BVN data for user {user.email} (retry for wallet creation)")

            # Reconstruct verification data from user model
            verification_data = {
                'firstName': user.bvn_first_name,
                'lastName': user.bvn_last_name,
                'dateOfBirth': user.bvn_dob,
                'phoneNumber': user.bvn_phone,
                'gender': user.bvn_gender,
                'stateOfResidence': user.bvn_state_of_residence,
                'enrollmentBank': user.bvn_enrollment_bank,
                'watchListed': user.bvn_watch_listed,
                'residentialAddress': user.bvn_residential_address,
            }
        else:
            # Call Prembly API to verify BVN
            logger.info(f"Verifying BVN for user {user.email} via Prembly")
            prembly_response = verify_bvn(bvn)

            if prembly_response.get("status") != "success":
                error_message = prembly_response.get("message", "BVN verification failed")
                logger.error(f"Prembly BVN verification failed for {user.email}: {error_message}")

                return Response({
                    "success": False,
                    "error": {
                        "code": "KYC_BVN_INVALID",
                        "message": error_message,
                        "data": prembly_response.get("details")
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Extract BVN data from Prembly response
            prembly_data = prembly_response.get("data", {})

            # Debug: Log the actual Prembly response structure
            logger.info(f"DEBUG - Raw Prembly response: {prembly_response}")
            logger.info(f"DEBUG - Prembly data: {prembly_data}")

            # Handle different Prembly response structures
            verification_data = prembly_data.get("data") or prembly_data.get("verification") or prembly_data

            logger.info(f"DEBUG - Extracted verification_data: {verification_data}")

        # Store verification result in cache for 10 minutes
        cache_key = f"bvn_verification_{user.id}"
        cache_data = {
            "bvn": bvn,
            "verification_data": verification_data,
            "timestamp": datetime.now().isoformat()
        }
        cache.set(cache_key, cache_data, timeout=600)  # 10 minutes

        logger.info(f"BVN verification successful for {user.email}, data cached")

        # Transform Prembly's camelCase fields to snake_case for frontend
        bvn_details = {
            'first_name': verification_data.get('firstName') or verification_data.get('firstname') or verification_data.get('first_name'),
            'last_name': verification_data.get('lastName') or verification_data.get('lastname') or verification_data.get('last_name'),
            'middle_name': verification_data.get('middleName') or verification_data.get('middlename') or verification_data.get('middle_name'),
            'date_of_birth': verification_data.get('dateOfBirth') or verification_data.get('birthdate') or verification_data.get('date_of_birth') or verification_data.get('dob'),
            'phone_number': verification_data.get('phoneNumber') or verification_data.get('phone') or verification_data.get('phone_number'),
            'email': verification_data.get('email'),
            'gender': verification_data.get('gender'),
            'state_of_residence': verification_data.get('stateOfResidence') or verification_data.get('state_of_residence') or verification_data.get('state'),
            'enrollment_bank': verification_data.get('enrollmentBank') or verification_data.get('enrollment_bank'),
            'watch_listed': verification_data.get('watchListed') or verification_data.get('watch_listed') or verification_data.get('watchlisted'),
        }

        # Return BVN details for user to review
        return Response({
            "success": True,
            "data": {
                "details": bvn_details,
                "message": "BVN verified successfully"
            }
        }, status=status.HTTP_200_OK)


class V2BVNConfirmView(APIView):
    """
    Step 2: Confirm BVN details and save to database
    Updates user verification status and account tier
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = V2BVNConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "data": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        bvn = serializer.validated_data['bvn']
        confirmed = serializer.validated_data['confirmed']

        # Retrieve cached verification data
        cache_key = f"bvn_verification_{user.id}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_SESSION_EXPIRED",
                    "message": "Verification session has expired. Please verify your BVN again"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify BVN matches cached data
        if cached_data.get("bvn") != bvn:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_BVN_MISMATCH",
                    "message": "BVN does not match verification session"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        verification_data = cached_data.get("verification_data", {})

        # Save BVN data to user model
        try:
            with transaction.atomic():
                user.bvn = bvn
                user.bvn_first_name = verification_data.get("firstName") or verification_data.get("firstname") or verification_data.get("first_name")
                user.bvn_last_name = verification_data.get("lastName") or verification_data.get("lastname") or verification_data.get("last_name")
                user.bvn_dob = verification_data.get("dateOfBirth") or verification_data.get("birthdate") or verification_data.get("date_of_birth") or verification_data.get("dob")
                user.bvn_gender = verification_data.get("gender")
                user.bvn_phone = verification_data.get("phoneNumber") or verification_data.get("phone") or verification_data.get("phone_number")
                user.bvn_marital_status = verification_data.get("maritalStatus") or verification_data.get("marital_status")
                user.bvn_nationality = verification_data.get("nationality")
                user.bvn_residential_address = verification_data.get("residentialAddress") or verification_data.get("residential_address") or verification_data.get("address")
                user.bvn_state_of_residence = verification_data.get("stateOfResidence") or verification_data.get("state_of_residence") or verification_data.get("state")
                user.bvn_watch_listed = str(verification_data.get("watchListed") or verification_data.get("watch_listed") or verification_data.get("watchlisted") or "")
                user.bvn_enrollment_bank = verification_data.get("enrollmentBank") or verification_data.get("enrollment_bank")

                # Store photo if available
                photo_url = verification_data.get("photo") or verification_data.get("image")
                if photo_url and not user.image:
                    user.image = photo_url

                user.has_bvn = True

                # Update account tier
                if user.has_bvn and user.has_nin:
                    user.account_tier = "Tier 2"
                    tier_message = "Both BVN and NIN verified! You now have Tier 2 access"
                    limits = {
                        "daily_limit": 100000000,  # NGN 100M
                        "per_transaction_limit": 50000000,  # NGN 50M
                        "monthly_limit": 1000000000  # NGN 1B
                    }
                elif user.has_bvn:
                    user.account_tier = "Tier 1"
                    tier_message = "BVN verified successfully! You now have Tier 1 access"
                    limits = {
                        "daily_limit": 50000000,  # NGN 50M
                        "per_transaction_limit": 20000000,  # NGN 20M
                        "monthly_limit": 500000000  # NGN 500M
                    }

                user.save()

                # Clear cache
                cache.delete(cache_key)

                logger.info(f"BVN confirmed and saved for user {user.email}, tier: {user.account_tier}")

                # Create 9PSB wallet if user doesn't have one yet (V2 flow)
                wallet_created = False
                wallet_account_number = None
                try:
                    wallet, created = Wallet.objects.get_or_create(user=user)

                    if created or not wallet.psb9_account_number:
                        # Prepare customer data for 9PSB wallet creation
                        # 9PSB requires gender as integer: 1 = Male, 2 = Female
                        gender_int = 1 if user.bvn_gender and user.bvn_gender.upper() in ["MALE", "M"] else 2

                        # Generate unique transaction tracking reference
                        tracking_ref = f"GIDINEST_WALLET_{user.id}_{uuid.uuid4().hex[:12].upper()}"

                        # Format date of birth to dd/mm/yyyy (9PSB requirement)
                        dob = user.bvn_dob if user.bvn_dob else user.dob
                        if isinstance(dob, str):
                            # Parse string date (could be YYYY-MM-DD or other format)
                            try:
                                from dateutil import parser
                                dob_obj = parser.parse(dob)
                                formatted_dob = dob_obj.strftime('%d/%m/%Y')
                            except:
                                # Fallback: assume YYYY-MM-DD format
                                try:
                                    dob_obj = datetime.strptime(dob, '%Y-%m-%d')
                                    formatted_dob = dob_obj.strftime('%d/%m/%Y')
                                except:
                                    formatted_dob = dob  # Use as-is if parsing fails
                        elif hasattr(dob, 'strftime'):
                            # Date or datetime object
                            formatted_dob = dob.strftime('%d/%m/%Y')
                        else:
                            formatted_dob = str(dob) if dob else ""

                        # 9PSB uses: lastName + otherNames for account name
                        # otherNames should be: firstName + middleName (if exists)
                        first_name = user.bvn_first_name or user.first_name or ""
                        middle_name = getattr(user, 'bvn_middle_name', '') or getattr(user, 'middle_name', '') or ""

                        # Combine first name and middle name for otherNames
                        other_names_parts = [name.strip() for name in [first_name, middle_name] if name and name.strip()]
                        other_names = " ".join(other_names_parts) if other_names_parts else " "

                        customer_data = {
                            "firstName": first_name,
                            "lastName": user.bvn_last_name or user.last_name,
                            "otherNames": other_names,
                            "phoneNo": user.bvn_phone or user.phone,  # 9PSB expects "phoneNo", not "phoneNumber"
                            "email": user.email,
                            "bvn": user.bvn,
                            "gender": gender_int,
                            "dateOfBirth": formatted_dob,  # 9PSB expects dd/mm/yyyy format
                            "address": user.bvn_residential_address or user.address or "Not Provided",
                            "transactionTrackingRef": tracking_ref
                        }

                        # Create wallet with 9PSB
                        logger.info(f"Creating 9PSB wallet for user {user.email}")
                        result = psb9_client.open_wallet(customer_data)

                        if result.get("status") == "success":
                            wallet_data = result.get("data", {})

                            # Update wallet with 9PSB details
                            # Note: 9PSB returns customerID (uppercase), fullName, and orderRef
                            wallet.provider_version = "v2"
                            wallet.psb9_customer_id = wallet_data.get("customerID") or wallet_data.get("customerId")
                            wallet.psb9_account_number = wallet_data.get("accountNumber")
                            wallet.psb9_wallet_id = wallet_data.get("orderRef") or wallet_data.get("walletId")
                            wallet.account_number = wallet_data.get("accountNumber")
                            wallet.account_name = wallet_data.get("fullName") or wallet_data.get("accountName")
                            wallet.bank = "9PSB"
                            wallet.bank_code = "120001"  # 9PSB bank code
                            wallet.save()

                            wallet_created = True
                            wallet_account_number = wallet.psb9_account_number
                            logger.info(f"9PSB wallet created successfully for {user.email}: {wallet_account_number}")
                        else:
                            error_msg = result.get("message", "Unknown error")
                            logger.error(f"Failed to create 9PSB wallet for {user.email}: {error_msg}")
                            # Don't fail the entire BVN confirmation if wallet creation fails
                            # User can retry wallet creation later

                except Exception as e:
                    logger.error(f"Error creating 9PSB wallet for user {user.email}: {str(e)}", exc_info=True)
                    # Don't fail the entire BVN confirmation if wallet creation fails

                # Prepare response data
                response_data = {
                    "is_verified": True,
                    "verification_method": "bvn",
                    "verification_status": "verified",
                    "account_tier": user.account_tier,
                    "message": tier_message,
                    "limits": limits
                }

                # Add wallet info to response if created
                if wallet_created and wallet_account_number:
                    response_data["wallet"] = {
                        "created": True,
                        "account_number": wallet_account_number,
                        "bank": "9PSB",
                        "message": "Virtual wallet created successfully! You can now receive deposits."
                    }

                return Response({
                    "success": True,
                    "data": response_data
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error saving BVN for user {user.email}: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Failed to save BVN verification. Please try again"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class V2NINVerifyView(APIView):
    """
    Step 1: Verify NIN with Prembly
    Returns NIN details for user review without saving to database
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = V2NINVerifySerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "data": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        nin = serializer.validated_data['nin']
        first_name = serializer.validated_data.get('first_name')
        last_name = serializer.validated_data.get('last_name')
        dob = serializer.validated_data.get('dob')

        # Check if NIN is already verified for this user
        if user.has_nin:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_NIN_ALREADY_VERIFIED",
                    "message": "NIN has already been verified for this account"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if NIN is used by another account
        # Skip duplicate check in DEBUG mode for testing
        if not settings.DEBUG:
            if UserModel.objects.filter(nin=nin).exclude(id=user.id).exists():
                return Response({
                    "success": False,
                    "error": {
                        "code": "KYC_NIN_DUPLICATE",
                        "message": "This NIN has already been used for another account"
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # In DEBUG mode, allow duplicate NINs but log a warning
            if UserModel.objects.filter(nin=nin).exclude(id=user.id).exists():
                logger.warning(f"TEST MODE: Allowing duplicate NIN {nin} for user {user.email}")

        # Call Prembly API to verify NIN
        logger.info(f"Verifying NIN for user {user.email} via Prembly")
        prembly_response = verify_nin(nin, first_name, last_name, dob)

        if prembly_response.get("status") != "success":
            error_message = prembly_response.get("message", "NIN verification failed")
            logger.error(f"Prembly NIN verification failed for {user.email}: {error_message}")

            return Response({
                "success": False,
                "error": {
                    "code": "KYC_NIN_INVALID",
                    "message": error_message,
                    "data": prembly_response.get("details")
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Extract NIN data from Prembly response
        prembly_data = prembly_response.get("data", {})

        # Handle different Prembly response structures
        verification_data = prembly_data.get("data") or prembly_data.get("verification") or prembly_data

        # Store verification result in cache for 10 minutes
        cache_key = f"nin_verification_{user.id}"
        cache_data = {
            "nin": nin,
            "verification_data": verification_data,
            "timestamp": datetime.now().isoformat()
        }
        cache.set(cache_key, cache_data, timeout=600)  # 10 minutes

        logger.info(f"NIN verification successful for {user.email}, data cached")

        # Transform Prembly's camelCase fields to snake_case for frontend
        nin_details = {
            'first_name': verification_data.get('firstName') or verification_data.get('firstname') or verification_data.get('first_name'),
            'last_name': verification_data.get('lastName') or verification_data.get('lastname') or verification_data.get('last_name'),
            'middle_name': verification_data.get('middleName') or verification_data.get('middlename') or verification_data.get('middle_name'),
            'date_of_birth': verification_data.get('dateOfBirth') or verification_data.get('birthdate') or verification_data.get('date_of_birth') or verification_data.get('dob'),
            'gender': verification_data.get('gender'),
            'state_of_origin': verification_data.get('stateOfOrigin') or verification_data.get('state_of_origin') or verification_data.get('state'),
            'lga': verification_data.get('lga') or verification_data.get('localGovernment') or verification_data.get('local_government'),
            'address': verification_data.get('residentialAddress') or verification_data.get('address') or verification_data.get('residential_address'),
            'phone': verification_data.get('phoneNumber') or verification_data.get('phone') or verification_data.get('phone_number'),
        }

        # Return NIN details for user to review
        return Response({
            "success": True,
            "data": {
                "details": nin_details,
                "message": "NIN verified successfully"
            }
        }, status=status.HTTP_200_OK)


class V2NINConfirmView(APIView):
    """
    Step 2: Confirm NIN details and save to database
    Updates user verification status and account tier
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = V2NINConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "data": serializer.errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        nin = serializer.validated_data['nin']
        confirmed = serializer.validated_data['confirmed']

        # Retrieve cached verification data
        cache_key = f"nin_verification_{user.id}"
        cached_data = cache.get(cache_key)

        if not cached_data:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_SESSION_EXPIRED",
                    "message": "Verification session has expired. Please verify your NIN again"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verify NIN matches cached data
        if cached_data.get("nin") != nin:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_NIN_MISMATCH",
                    "message": "NIN does not match verification session"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        verification_data = cached_data.get("verification_data", {})

        # Save NIN data to user model
        try:
            with transaction.atomic():
                user.nin = nin
                user.nin_first_name = verification_data.get("firstName") or verification_data.get("firstname") or verification_data.get("first_name")
                user.nin_last_name = verification_data.get("lastName") or verification_data.get("lastname") or verification_data.get("last_name")
                user.nin_dob = verification_data.get("dateOfBirth") or verification_data.get("birthdate") or verification_data.get("date_of_birth") or verification_data.get("dob")
                user.nin_gender = verification_data.get("gender")
                user.nin_phone = verification_data.get("phoneNumber") or verification_data.get("phone") or verification_data.get("phone_number")
                user.nin_marital_status = verification_data.get("maritalStatus") or verification_data.get("marital_status")
                user.nin_nationality = verification_data.get("nationality")
                user.nin_residential_address = verification_data.get("residentialAddress") or verification_data.get("residential_address") or verification_data.get("address")
                user.nin_state_of_residence = verification_data.get("stateOfOrigin") or verification_data.get("state_of_origin") or verification_data.get("state")

                user.has_nin = True

                # Update account tier
                if user.has_bvn and user.has_nin:
                    user.account_tier = "Tier 2"
                    tier_message = "Both BVN and NIN verified! You now have Tier 2 access"
                    limits = {
                        "daily_limit": 100000000,  # NGN 100M
                        "per_transaction_limit": 50000000,  # NGN 50M
                        "monthly_limit": 1000000000  # NGN 1B
                    }
                elif user.has_nin:
                    user.account_tier = "Tier 1"
                    tier_message = "NIN verified successfully! You now have Tier 1 access"
                    limits = {
                        "daily_limit": 50000000,  # NGN 50M
                        "per_transaction_limit": 20000000,  # NGN 20M
                        "monthly_limit": 500000000  # NGN 500M
                    }

                user.save()

                # Clear cache
                cache.delete(cache_key)

                logger.info(f"NIN confirmed and saved for user {user.email}, tier: {user.account_tier}")

                return Response({
                    "success": True,
                    "data": {
                        "is_verified": True,
                        "verification_method": "nin",
                        "verification_status": "verified",
                        "account_tier": user.account_tier,
                        "message": tier_message,
                        "limits": limits
                    }
                }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error saving NIN for user {user.email}: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Failed to save NIN verification. Please try again"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class V2WalletSyncView(APIView):
    """
    Manually sync wallet details from known 9PSB data.

    This endpoint is used when:
    - Wallet was created in 9PSB but not saved to database
    - Need to manually update wallet record with 9PSB details
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if user has verified BVN
        if not user.has_bvn or not user.bvn:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_BVN_NOT_VERIFIED",
                    "message": "Please verify your BVN first"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get wallet details from request (or use defaults for this user)
        account_number = request.data.get('account_number', '1100072011')
        customer_id = request.data.get('customer_id', '007201')

        # Construct account name from user details
        first_name = user.bvn_first_name or user.first_name or ""
        middle_name = getattr(user, 'bvn_middle_name', '') or ""
        last_name = user.bvn_last_name or user.last_name or ""

        other_names_parts = [name.strip() for name in [first_name, middle_name] if name and name.strip()]
        other_names = " ".join(other_names_parts) if other_names_parts else ""
        account_name = f"GIDINEST/{last_name.upper()} {other_names.upper()}" if last_name else ""

        try:
            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=user)

            # Update wallet with 9PSB details
            wallet.provider_version = "v2"
            wallet.psb9_customer_id = customer_id
            wallet.psb9_account_number = account_number
            wallet.psb9_wallet_id = account_number  # orderRef same as account number
            wallet.account_number = account_number
            wallet.account_name = account_name or request.data.get('account_name', '')
            wallet.bank = "9PSB"
            wallet.bank_code = "120001"
            wallet.save()

            # Update user flag
            if not user.has_virtual_wallet:
                user.has_virtual_wallet = True
                user.save()

            logger.info(f"Wallet synced for {user.email}: {wallet.account_number}")

            return Response({
                "success": True,
                "data": {
                    "wallet": {
                        "account_number": wallet.account_number,
                        "account_name": wallet.account_name,
                        "bank": wallet.bank,
                        "bank_code": wallet.bank_code,
                        "customer_id": wallet.psb9_customer_id
                    },
                    "message": "Wallet details synced successfully"
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error syncing wallet for {user.email}: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Failed to sync wallet details"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class V2WalletRetryView(APIView):
    """
    Retry wallet creation for users who have verified BVN but wallet creation failed.

    This endpoint handles edge cases where:
    - User completed BVN verification successfully
    - But 9PSB wallet creation failed (network, API error, etc.)
    - User needs to retry wallet creation without re-verifying BVN
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user

        # Check if user has verified BVN
        if not user.has_bvn or not user.bvn:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_BVN_NOT_VERIFIED",
                    "message": "Please verify your BVN first before creating a wallet"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if wallet already exists with 9PSB account
        try:
            wallet = user.wallet
            if wallet.psb9_account_number:
                return Response({
                    "success": False,
                    "error": {
                        "code": "WALLET_ALREADY_EXISTS",
                        "message": "Wallet already created for this account",
                        "data": {
                            "account_number": wallet.psb9_account_number,
                            "bank": "9PSB"
                        }
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
        except Wallet.DoesNotExist:
            # No wallet exists, we'll create one
            pass

        # Attempt to create wallet using stored BVN data
        try:
            with transaction.atomic():
                wallet, created = Wallet.objects.get_or_create(user=user)

                # Prepare customer data for 9PSB wallet creation
                # 9PSB requires gender as integer: 1 = Male, 2 = Female
                gender_int = 1 if user.bvn_gender and user.bvn_gender.upper() in ["MALE", "M"] else 2

                # Generate unique transaction tracking reference
                tracking_ref = f"GIDINEST_WALLET_RETRY_{user.id}_{uuid.uuid4().hex[:12].upper()}"

                # Format date of birth to dd/mm/yyyy (9PSB requirement)
                dob = user.bvn_dob if user.bvn_dob else user.dob
                if isinstance(dob, str):
                    # Parse string date (could be YYYY-MM-DD or other format)
                    try:
                        from dateutil import parser
                        dob_obj = parser.parse(dob)
                        formatted_dob = dob_obj.strftime('%d/%m/%Y')
                    except:
                        # Fallback: assume YYYY-MM-DD format
                        try:
                            dob_obj = datetime.strptime(dob, '%Y-%m-%d')
                            formatted_dob = dob_obj.strftime('%d/%m/%Y')
                        except:
                            formatted_dob = dob  # Use as-is if parsing fails
                elif hasattr(dob, 'strftime'):
                    # Date or datetime object
                    formatted_dob = dob.strftime('%d/%m/%Y')
                else:
                    formatted_dob = str(dob) if dob else ""

                # 9PSB uses: lastName + otherNames for account name
                # otherNames should be: firstName + middleName (if exists)
                first_name = user.bvn_first_name or user.first_name or ""
                middle_name = getattr(user, 'bvn_middle_name', '') or getattr(user, 'middle_name', '') or ""

                # Combine first name and middle name for otherNames
                other_names_parts = [name.strip() for name in [first_name, middle_name] if name and name.strip()]
                other_names = " ".join(other_names_parts) if other_names_parts else " "

                customer_data = {
                    "firstName": first_name,
                    "lastName": user.bvn_last_name or user.last_name,
                    "otherNames": other_names,
                    "phoneNo": user.bvn_phone or user.phone,  # 9PSB expects "phoneNo", not "phoneNumber"
                    "email": user.email,
                    "bvn": user.bvn,
                    "gender": gender_int,
                    "dateOfBirth": formatted_dob,  # 9PSB expects dd/mm/yyyy format
                    "address": user.bvn_residential_address or user.address or "Not Provided",
                    "transactionTrackingRef": tracking_ref
                }

                # Create wallet with 9PSB
                logger.info(f"Retrying 9PSB wallet creation for user {user.email}")
                result = psb9_client.open_wallet(customer_data)

                if result.get("status") == "success":
                    wallet_data = result.get("data", {})

                    # Update wallet with 9PSB details
                    # Note: 9PSB returns customerID (uppercase), fullName, and orderRef
                    wallet.provider_version = "v2"
                    wallet.psb9_customer_id = wallet_data.get("customerID") or wallet_data.get("customerId")
                    wallet.psb9_account_number = wallet_data.get("accountNumber")
                    wallet.psb9_wallet_id = wallet_data.get("orderRef") or wallet_data.get("walletId")
                    wallet.account_number = wallet_data.get("accountNumber")
                    wallet.account_name = wallet_data.get("fullName") or wallet_data.get("accountName")
                    wallet.bank = "9PSB"
                    wallet.bank_code = "120001"  # 9PSB bank code
                    wallet.save()

                    logger.info(f"9PSB wallet created successfully for {user.email}: {wallet.psb9_account_number}")

                    return Response({
                        "success": True,
                        "data": {
                            "wallet": {
                                "created": True,
                                "account_number": wallet.psb9_account_number,
                                "account_name": wallet.account_name,
                                "bank": "9PSB",
                                "message": "Virtual wallet created successfully! You can now receive deposits."
                            },
                            "account_tier": user.account_tier
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = result.get("message", "Unknown error")
                    error_details = result.get("details")
                    logger.error(f"Failed to create 9PSB wallet for {user.email}: {error_msg}")

                    return Response({
                        "success": False,
                        "error": {
                            "code": "WALLET_CREATION_FAILED",
                            "message": f"Failed to create wallet: {error_msg}",
                            "details": error_details
                        }
                    }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error retrying wallet creation for user {user.email}: {str(e)}", exc_info=True)
            return Response({
                "success": False,
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "Failed to create wallet. Please try again later"
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

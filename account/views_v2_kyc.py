"""
V2 KYC Views - Prembly Integration
Two-step BVN and NIN verification flow for mobile app
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.cache import cache
from django.db import transaction
from datetime import datetime
import logging

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
        if user.has_bvn:
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_BVN_ALREADY_VERIFIED",
                    "message": "BVN has already been verified for this account"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Check if BVN is used by another account
        if UserModel.objects.filter(bvn=bvn).exclude(id=user.id).exists():
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_BVN_DUPLICATE",
                    "message": "This BVN has already been used for another account"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # Handle different Prembly response structures
        verification_data = prembly_data.get("data") or prembly_data.get("verification") or prembly_data

        # Store verification result in cache for 10 minutes
        cache_key = f"bvn_verification_{user.id}"
        cache_data = {
            "bvn": bvn,
            "verification_data": verification_data,
            "timestamp": datetime.now().isoformat()
        }
        cache.set(cache_key, cache_data, timeout=600)  # 10 minutes

        logger.info(f"BVN verification successful for {user.email}, data cached")

        # Return BVN details for user to review
        return Response({
            "success": True,
            "data": {
                "details": {
                    "first_name": verification_data.get("firstname") or verification_data.get("first_name"),
                    "last_name": verification_data.get("lastname") or verification_data.get("last_name"),
                    "middle_name": verification_data.get("middlename") or verification_data.get("middle_name"),
                    "date_of_birth": verification_data.get("birthdate") or verification_data.get("date_of_birth") or verification_data.get("dob"),
                    "phone_number": verification_data.get("phone") or verification_data.get("phone_number"),
                    "email": verification_data.get("email"),
                    "gender": verification_data.get("gender"),
                    "state_of_residence": verification_data.get("state_of_residence") or verification_data.get("state"),
                    "enrollment_bank": verification_data.get("enrollment_bank"),
                    "watch_listed": verification_data.get("watch_listed") or verification_data.get("watchlisted"),
                }
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
                user.bvn_first_name = verification_data.get("firstname") or verification_data.get("first_name")
                user.bvn_last_name = verification_data.get("lastname") or verification_data.get("last_name")
                user.bvn_dob = verification_data.get("birthdate") or verification_data.get("date_of_birth") or verification_data.get("dob")
                user.bvn_gender = verification_data.get("gender")
                user.bvn_phone = verification_data.get("phone") or verification_data.get("phone_number")
                user.bvn_marital_status = verification_data.get("marital_status")
                user.bvn_nationality = verification_data.get("nationality")
                user.bvn_residential_address = verification_data.get("residential_address") or verification_data.get("address")
                user.bvn_state_of_residence = verification_data.get("state_of_residence") or verification_data.get("state")
                user.bvn_watch_listed = str(verification_data.get("watch_listed") or verification_data.get("watchlisted") or "")
                user.bvn_enrollment_bank = verification_data.get("enrollment_bank")

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
                        customer_data = {
                            "firstName": user.bvn_first_name or user.first_name,
                            "lastName": user.bvn_last_name or user.last_name,
                            "phoneNumber": user.bvn_phone or user.phone,
                            "email": user.email,
                            "bvn": user.bvn,
                            "gender": "M" if user.bvn_gender and user.bvn_gender.upper() in ["MALE", "M"] else "F",
                            "dateOfBirth": user.bvn_dob if user.bvn_dob else user.dob,
                            "address": user.bvn_residential_address or user.address or "Not Provided"
                        }

                        # Create wallet with 9PSB
                        logger.info(f"Creating 9PSB wallet for user {user.email}")
                        result = psb9_client.open_wallet(customer_data)

                        if result.get("status") == "success":
                            wallet_data = result.get("data", {})

                            # Update wallet with 9PSB details
                            wallet.provider_version = "v2"
                            wallet.psb9_customer_id = wallet_data.get("customerId")
                            wallet.psb9_account_number = wallet_data.get("accountNumber")
                            wallet.psb9_wallet_id = wallet_data.get("walletId")
                            wallet.account_number = wallet_data.get("accountNumber")
                            wallet.account_name = wallet_data.get("accountName")
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
        if UserModel.objects.filter(nin=nin).exclude(id=user.id).exists():
            return Response({
                "success": False,
                "error": {
                    "code": "KYC_NIN_DUPLICATE",
                    "message": "This NIN has already been used for another account"
                }
            }, status=status.HTTP_400_BAD_REQUEST)

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

        # Return NIN details for user to review
        return Response({
            "success": True,
            "data": {
                "details": {
                    "first_name": verification_data.get("firstname") or verification_data.get("first_name"),
                    "last_name": verification_data.get("lastname") or verification_data.get("last_name"),
                    "middle_name": verification_data.get("middlename") or verification_data.get("middle_name"),
                    "date_of_birth": verification_data.get("birthdate") or verification_data.get("date_of_birth") or verification_data.get("dob"),
                    "gender": verification_data.get("gender"),
                    "state_of_origin": verification_data.get("state_of_origin") or verification_data.get("state"),
                    "lga": verification_data.get("lga") or verification_data.get("local_government"),
                    "address": verification_data.get("address") or verification_data.get("residential_address"),
                    "phone": verification_data.get("phone") or verification_data.get("phone_number"),
                }
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
                user.nin_first_name = verification_data.get("firstname") or verification_data.get("first_name")
                user.nin_last_name = verification_data.get("lastname") or verification_data.get("last_name")
                user.nin_dob = verification_data.get("birthdate") or verification_data.get("date_of_birth") or verification_data.get("dob")
                user.nin_gender = verification_data.get("gender")
                user.nin_phone = verification_data.get("phone") or verification_data.get("phone_number")
                user.nin_marital_status = verification_data.get("marital_status")
                user.nin_nationality = verification_data.get("nationality")
                user.nin_residential_address = verification_data.get("residential_address") or verification_data.get("address")
                user.nin_state_of_residence = verification_data.get("state_of_origin") or verification_data.get("state")

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

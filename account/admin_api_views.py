"""
Admin API views for internal operations
Requires staff/admin authentication
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.db.models import Q
from account.models import UserModel
from wallet.models import Wallet
import logging

logger = logging.getLogger(__name__)


class IsAdminUser(permissions.BasePermission):
    """
    Permission class to ensure only admin users can access
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


class AdminWalletFixView(APIView):
    """
    Admin endpoint to fix wallet issues for users

    Operations:
    1. Fix has_virtual_wallet flag for users with wallets
    2. List users with wallet issues
    3. Bulk fix all affected users
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Get list of users with wallet issues
        """
        operation = request.query_params.get('operation', 'list')

        if operation == 'list':
            # Find users with wallet data but has_virtual_wallet=False
            users_with_wallet_flag_issue = UserModel.objects.filter(
                has_virtual_wallet=False,
                wallet__account_number__isnull=False
            ).select_related('wallet').values(
                'id', 'email', 'first_name', 'last_name',
                'wallet__account_number', 'wallet__account_name',
                'wallet__bank', 'has_bvn'
            )

            # Find users with BVN but no wallet record
            users_with_bvn_no_wallet = UserModel.objects.filter(
                has_bvn=True,
                has_virtual_wallet=False
            ).filter(
                Q(wallet__isnull=True) | Q(wallet__account_number__isnull=True)
            ).values(
                'id', 'email', 'first_name', 'last_name', 'has_bvn'
            )

            return Response({
                "success": True,
                "data": {
                    "users_with_flag_issue": list(users_with_wallet_flag_issue),
                    "users_with_bvn_no_wallet": list(users_with_bvn_no_wallet),
                    "summary": {
                        "flag_issue_count": len(users_with_wallet_flag_issue),
                        "bvn_no_wallet_count": len(users_with_bvn_no_wallet)
                    }
                }
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "error": "Invalid operation"
        }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
        Fix wallet issues

        Body:
        {
            "operation": "fix_flags",  // or "fix_single_user"
            "user_id": 123  // optional, for single user fix
        }
        """
        operation = request.data.get('operation')
        user_id = request.data.get('user_id')

        if operation == 'fix_flags':
            # Fix has_virtual_wallet flag for all users with wallet data
            try:
                with transaction.atomic():
                    # Get users with wallets but flag not set
                    users_to_fix = UserModel.objects.filter(
                        has_virtual_wallet=False,
                        wallet__account_number__isnull=False
                    )

                    count = users_to_fix.count()

                    # Update the flag
                    updated = users_to_fix.update(has_virtual_wallet=True)

                    logger.info(f"Admin {request.user.email} fixed has_virtual_wallet flag for {updated} users")

                    return Response({
                        "success": True,
                        "data": {
                            "operation": "fix_flags",
                            "users_fixed": updated,
                            "message": f"Successfully updated has_virtual_wallet flag for {updated} users"
                        }
                    }, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error fixing wallet flags: {str(e)}", exc_info=True)
                return Response({
                    "success": False,
                    "error": {
                        "code": "FIX_FAILED",
                        "message": f"Failed to fix wallet flags: {str(e)}"
                    }
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        elif operation == 'fix_single_user':
            # Fix flag for a single user
            if not user_id:
                return Response({
                    "success": False,
                    "error": "user_id is required for single user fix"
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = UserModel.objects.get(id=user_id)

                # Check if user has wallet
                try:
                    wallet = user.wallet
                    if wallet.account_number:
                        user.has_virtual_wallet = True
                        user.save()

                        logger.info(f"Admin {request.user.email} fixed wallet flag for user {user.email}")

                        return Response({
                            "success": True,
                            "data": {
                                "operation": "fix_single_user",
                                "user_id": user.id,
                                "user_email": user.email,
                                "wallet_account": wallet.account_number,
                                "message": "Successfully updated has_virtual_wallet flag"
                            }
                        }, status=status.HTTP_200_OK)
                    else:
                        return Response({
                            "success": False,
                            "error": "User has wallet record but no account number"
                        }, status=status.HTTP_400_BAD_REQUEST)

                except Wallet.DoesNotExist:
                    return Response({
                        "success": False,
                        "error": "User has no wallet record"
                    }, status=status.HTTP_404_NOT_FOUND)

            except UserModel.DoesNotExist:
                return Response({
                    "success": False,
                    "error": "User not found"
                }, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                logger.error(f"Error fixing wallet flag for user {user_id}: {str(e)}", exc_info=True)
                return Response({
                    "success": False,
                    "error": f"Failed to fix wallet flag: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "success": False,
            "error": "Invalid operation. Use 'fix_flags' or 'fix_single_user'"
        }, status=status.HTTP_400_BAD_REQUEST)

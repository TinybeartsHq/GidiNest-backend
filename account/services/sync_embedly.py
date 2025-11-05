"""
Service for syncing user verification status from Embedly to local database.
"""
from typing import Dict, Any, List
from account.models.users import UserModel
from providers.helpers.embedly import EmbedlyClient
import logging

logger = logging.getLogger(__name__)


class EmbedlySyncService:
    """
    Service to sync user verification status from Embedly back to local database.
    """

    def __init__(self):
        self.embedly_client = EmbedlyClient()

    def sync_user_verification(self, user: UserModel) -> Dict[str, Any]:
        """
        Sync a single user's verification status from Embedly.

        Args:
            user (UserModel): The user to sync

        Returns:
            Dict with sync result
        """
        if not user.embedly_customer_id:
            return {
                "success": False,
                "user_id": user.id,
                "email": user.email,
                "message": "No embedly customer ID found"
            }

        try:
            # Get customer info from Embedly
            embedly_response = self.embedly_client.get_customer(user.embedly_customer_id)

            if not embedly_response.get("success"):
                error_msg = embedly_response.get("message", "Failed to fetch from Embedly")
                error_code = embedly_response.get("code", "unknown")
                error_data = embedly_response.get("data", {})

                # Log with more detail
                logger.error(
                    f"Failed to fetch embedly data for user {user.email} "
                    f"(customer_id: {user.embedly_customer_id}): "
                    f"Error: {error_msg}, Code: {error_code}, Data: {error_data}"
                )

                return {
                    "success": False,
                    "user_id": user.id,
                    "email": user.email,
                    "message": f"{error_msg} (Code: {error_code})",
                    "error_details": error_data
                }

            # Extract customer data
            customer_data = embedly_response.get("data", {})

            # Track what changed
            changes = []
            old_tier = user.account_tier

            # Check KYC status from Embedly
            kyc_level = customer_data.get("kycLevel", 0)
            kyc_status = customer_data.get("kycStatus", "")

            # Determine verification status based on KYC level
            # Level 0 = No verification
            # Level 1 = Basic KYC (BVN or NIN)
            # Level 2 = Enhanced KYC (BVN and NIN)
            # Level 3 = Full KYC (with address)

            updated = False

            # Sync BVN/NIN verification status from Embedly
            # Check verification details from Embedly response
            # Look for actual verification data (BVN/NIN numbers or verification flags)

            # Check if Embedly customer data has BVN or NIN info
            customer_bvn = customer_data.get("bvn", "")
            customer_nin = customer_data.get("nin", "")
            verification_records = customer_data.get("verificationRecords", [])

            # Sync BVN status
            # User has BVN if: they have a BVN value in Embedly OR KYC level suggests it
            if customer_bvn:
                if not user.has_bvn:
                    user.has_bvn = True
                    changes.append("BVN verification synced from Embedly (found BVN data)")
                    updated = True
                    logger.info(f"User {user.email}: Set has_bvn=True (found BVN in Embedly)")

            # Sync NIN status
            # User has NIN if: they have a NIN value in Embedly
            if customer_nin:
                if not user.has_nin:
                    user.has_nin = True
                    changes.append("NIN verification synced from Embedly (found NIN data)")
                    updated = True
                    logger.info(f"User {user.email}: Set has_nin=True (found NIN in Embedly)")

            # Fallback: If KYC level >= 2, they must have both BVN and NIN
            # (Embedly requires both for Tier 2)
            if kyc_level >= 2:
                if not user.has_bvn:
                    user.has_bvn = True
                    changes.append("BVN verification synced (KYC Level 2+)")
                    updated = True
                    logger.info(f"User {user.email}: Set has_bvn=True (KYC level 2+)")

                if not user.has_nin:
                    user.has_nin = True
                    changes.append("NIN verification synced (KYC Level 2+)")
                    updated = True
                    logger.info(f"User {user.email}: Set has_nin=True (KYC level 2+)")

            # Fallback: If KYC level is 1 but we couldn't determine which one
            # Log it for manual review, don't assume
            elif kyc_level >= 1 and not user.has_bvn and not user.has_nin:
                logger.warning(
                    f"User {user.email} has KYC level {kyc_level} but we couldn't determine "
                    f"if it's BVN or NIN. Manual review needed. Embedly data: {customer_data.keys()}"
                )

            # Update account tier based on actual BVN/NIN verification status
            # Tier 1 = has BVN OR has NIN (at least one)
            # Tier 2 = has BVN AND has NIN (both)
            # Tier 3 = Tier 2 + address verification (based on KYC level 3)
            new_tier = self._determine_tier_from_verification_status(
                user.has_bvn,
                user.has_nin,
                kyc_level
            )

            if new_tier != user.account_tier:
                user.account_tier = new_tier
                changes.append(f"Tier: {old_tier} -> {new_tier}")
                updated = True

            # Check wallet status and sync wallet details
            has_wallet = customer_data.get("hasWallet", False) or bool(customer_data.get("wallets"))
            wallets_data = customer_data.get("wallets", [])

            # Sync has_virtual_wallet flag
            if has_wallet != user.has_virtual_wallet:
                user.has_virtual_wallet = has_wallet
                changes.append(f"Has wallet: {user.has_virtual_wallet} -> {has_wallet}")
                updated = True

            # If Embedly says user has wallet but our DB doesn't, sync wallet details
            if has_wallet and wallets_data:
                from wallet.models import Wallet

                try:
                    wallet = user.wallet
                except Wallet.DoesNotExist:
                    wallet = None

                # Get first wallet from Embedly
                embedly_wallet = wallets_data[0]
                wallet_id = embedly_wallet.get("id")
                virtual_account = embedly_wallet.get("virtualAccount", {})
                account_number = virtual_account.get("accountNumber")
                bank_name = virtual_account.get("bankName")
                bank_code = virtual_account.get("bankCode")

                # Create or update wallet if we have account number
                if account_number and (not wallet or not wallet.account_number):
                    if not wallet:
                        wallet = Wallet.objects.create(user=user)
                        changes.append("Created wallet from Embedly data")
                        logger.info(f"Created wallet for {user.email} from Embedly sync")

                    wallet.account_name = f"{user.first_name} {user.last_name}"
                    wallet.account_number = account_number
                    wallet.bank = bank_name
                    wallet.bank_code = bank_code
                    wallet.embedly_wallet_id = wallet_id
                    wallet.save()
                    changes.append(f"Synced wallet details (Account: {account_number})")
                    updated = True

                    # Also update user's embedly_wallet_id
                    if wallet_id and user.embedly_wallet_id != wallet_id:
                        user.embedly_wallet_id = wallet_id
                        changes.append("Synced embedly_wallet_id")
                        updated = True

            if updated:
                user.save()
                logger.info(f"Synced user {user.email}: {', '.join(changes)}")

            return {
                "success": True,
                "user_id": user.id,
                "email": user.email,
                "updated": updated,
                "changes": changes,
                "kyc_level": kyc_level,
                "current_tier": user.account_tier
            }

        except Exception as e:
            logger.error(f"Error syncing user {user.email}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "user_id": user.id,
                "email": user.email,
                "message": f"Error: {str(e)}"
            }

    def sync_all_users(self, limit: int = None) -> Dict[str, Any]:
        """
        Sync verification status for all users with embedly_customer_id.

        Args:
            limit (int): Optional limit on number of users to sync

        Returns:
            Dict with summary of sync results
        """
        # Get users with embedly customer IDs
        users_query = UserModel.objects.filter(
            embedly_customer_id__isnull=False
        ).exclude(embedly_customer_id="")

        if limit:
            users_query = users_query[:limit]

        users = list(users_query)
        total_users = len(users)

        results = {
            "total_users": total_users,
            "successful": 0,
            "failed": 0,
            "updated": 0,
            "no_changes": 0,
            "details": []
        }

        logger.info(f"Starting embedly sync for {total_users} users")

        for user in users:
            sync_result = self.sync_user_verification(user)
            results["details"].append(sync_result)

            if sync_result["success"]:
                results["successful"] += 1
                if sync_result.get("updated"):
                    results["updated"] += 1
                else:
                    results["no_changes"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Embedly sync completed. "
            f"Total: {total_users}, "
            f"Successful: {results['successful']}, "
            f"Failed: {results['failed']}, "
            f"Updated: {results['updated']}"
        )

        return results

    def sync_users_by_email(self, emails: List[str]) -> Dict[str, Any]:
        """
        Sync specific users by their email addresses.

        Args:
            emails (List[str]): List of email addresses to sync

        Returns:
            Dict with summary of sync results
        """
        users = UserModel.objects.filter(email__in=emails)

        results = {
            "total_users": len(emails),
            "found_users": users.count(),
            "successful": 0,
            "failed": 0,
            "updated": 0,
            "details": []
        }

        for user in users:
            sync_result = self.sync_user_verification(user)
            results["details"].append(sync_result)

            if sync_result["success"]:
                results["successful"] += 1
                if sync_result.get("updated"):
                    results["updated"] += 1
            else:
                results["failed"] += 1

        return results

    def _determine_tier_from_verification_status(
        self, has_bvn: bool, has_nin: bool, kyc_level: int
    ) -> str:
        """
        Determine account tier based on actual BVN/NIN verification status.

        Business Rules:
        - Tier 1 = has BVN OR has NIN (at least one verified)
        - Tier 2 = has BVN AND has NIN (both verified)
        - Tier 3 = Tier 2 + address verification (KYC level 3)

        Args:
            has_bvn (bool): Whether user has verified BVN
            has_nin (bool): Whether user has verified NIN
            kyc_level (int): The KYC level from Embedly

        Returns:
            str: Account tier
        """
        # Tier 3 requires both verifications + address (KYC level 3)
        if kyc_level >= 3 and has_bvn and has_nin:
            return "Tier 3"

        # Tier 2 requires both BVN and NIN
        if has_bvn and has_nin:
            return "Tier 2"

        # Tier 1 requires at least one (BVN or NIN)
        if has_bvn or has_nin:
            return "Tier 1"

        # Default tier for unverified users
        return "Tier 1"

    def _determine_tier_from_kyc_level(self, kyc_level: int) -> str:
        """
        Determine account tier based on Embedly KYC level.
        (Deprecated: Use _determine_tier_from_verification_status instead)

        Args:
            kyc_level (int): The KYC level from Embedly

        Returns:
            str: Account tier
        """
        if kyc_level >= 3:
            return "Tier 3"
        elif kyc_level >= 2:
            return "Tier 2"
        elif kyc_level >= 1:
            return "Tier 1"
        else:
            return "Tier 1"  # Default tier

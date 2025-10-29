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
                logger.error(f"Failed to fetch embedly data for user {user.email}: {embedly_response.get('message')}")
                return {
                    "success": False,
                    "user_id": user.id,
                    "email": user.email,
                    "message": embedly_response.get("message", "Failed to fetch from Embedly")
                }

            # Extract customer data
            customer_data = embedly_response.get("data", {})

            # Track what changed
            changes = []
            old_tier = user.account_tier

            # Check KYC status from Embedly
            kyc_level = customer_data.get("kycLevel", 0)

            # Determine verification status based on KYC level
            # Level 0 = No verification
            # Level 1 = Basic KYC (BVN or NIN)
            # Level 2 = Enhanced KYC (BVN and NIN)
            # Level 3 = Full KYC (with address)

            updated = False

            # Sync has_bvn if we detect BVN data in embedly response
            # Note: Embedly may not return exact BVN/NIN status, but we can infer from KYC level
            if kyc_level >= 1 and not user.has_bvn and not user.has_nin:
                # If KYC level is 1+, they have at least one verification
                # We need to make an educated guess or log for manual review
                logger.info(f"User {user.email} has KYC level {kyc_level} but local DB shows no verification")

            # Update account tier based on KYC level
            new_tier = self._determine_tier_from_kyc_level(kyc_level)

            if new_tier != user.account_tier:
                user.account_tier = new_tier
                changes.append(f"Tier: {old_tier} -> {new_tier}")
                updated = True

            # Check wallet status
            has_wallet = customer_data.get("hasWallet", False) or bool(customer_data.get("wallets"))
            if has_wallet != user.has_virtual_wallet:
                user.has_virtual_wallet = has_wallet
                changes.append(f"Has wallet: {user.has_virtual_wallet} -> {has_wallet}")
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

    def _determine_tier_from_kyc_level(self, kyc_level: int) -> str:
        """
        Determine account tier based on Embedly KYC level.

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

#!/usr/bin/env python
"""
Management command to check status of pending/processing withdrawals.
Run this as a cron job every 15-30 minutes to catch any missed webhooks.

Usage:
    python manage.py check_pending_withdrawals
    python manage.py check_pending_withdrawals --older-than-hours 2
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from wallet.models import WithdrawalRequest
from providers.helpers.embedly import EmbedlyClient
from notification.helper.email import MailClient
from providers.helpers.cuoral import CuoralAPI

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check status of pending/processing withdrawals via Embedly API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than-hours',
            type=int,
            default=1,
            help='Only check withdrawals older than X hours (default: 1)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of withdrawals to check (default: 50)'
        )

    def handle(self, *args, **options):
        older_than_hours = options['older_than_hours']
        limit = options['limit']

        cutoff_time = timezone.now() - timedelta(hours=older_than_hours)

        self.stdout.write('=' * 70)
        self.stdout.write(f'Checking Pending/Processing Withdrawals')
        self.stdout.write(f'Older than: {older_than_hours} hour(s)')
        self.stdout.write('=' * 70)

        # Find pending/processing withdrawals with transaction_ref
        pending_withdrawals = WithdrawalRequest.objects.filter(
            status__in=['pending', 'processing'],
            transaction_ref__isnull=False,
            created_at__lt=cutoff_time
        ).order_by('created_at')[:limit]

        if not pending_withdrawals.exists():
            self.stdout.write(self.style.SUCCESS('✅ No pending withdrawals to check'))
            return

        self.stdout.write(f'\nFound {pending_withdrawals.count()} withdrawal(s) to check\n')

        embedly_client = EmbedlyClient()
        updated_count = 0
        failed_count = 0
        completed_count = 0

        for withdrawal in pending_withdrawals:
            self.stdout.write(f'Checking withdrawal #{withdrawal.id} (Ref: {withdrawal.transaction_ref})...')

            try:
                # Query Embedly for status
                result = embedly_client.get_transfer_status(withdrawal.transaction_ref)

                if not result.get("success"):
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ API Error: {result.get("message")}')
                    )
                    failed_count += 1
                    continue

                # Extract status from response
                transfer_data = result.get("data", {})
                status_value = transfer_data.get("status", "").lower()

                old_status = withdrawal.status

                # Update based on status
                if status_value in ['successful', 'success', 'completed']:
                    withdrawal.status = 'completed'
                    withdrawal.save()

                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Completed: {old_status} → completed')
                    )

                    # Send notification to user
                    try:
                        self._notify_user_success(withdrawal)
                    except Exception as notif_error:
                        logger.error(f"Failed to notify user {withdrawal.user.email}: {notif_error}")

                    completed_count += 1
                    updated_count += 1

                elif status_value in ['failed', 'error', 'reversed']:
                    withdrawal.status = 'failed'
                    withdrawal.error_message = transfer_data.get('message', 'Transfer failed')
                    withdrawal.save()

                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Failed: {old_status} → failed')
                    )

                    # Refund user
                    try:
                        self._refund_user(withdrawal)
                    except Exception as refund_error:
                        logger.error(f"Failed to refund user {withdrawal.user.email}: {refund_error}")

                    failed_count += 1
                    updated_count += 1

                elif status_value in ['pending', 'processing']:
                    self.stdout.write(f'  ⏳ Still processing...')

                else:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Unknown status: {status_value}')
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Exception: {str(e)}')
                )
                logger.error(f"Error checking withdrawal {withdrawal.id}: {str(e)}", exc_info=True)
                failed_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'Summary:'))
        self.stdout.write(f'  Checked: {pending_withdrawals.count()}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Completed: {completed_count}')
        self.stdout.write(f'  Failed: {failed_count}')
        self.stdout.write('=' * 70)

    def _notify_user_success(self, withdrawal):
        """Send success notification to user"""
        try:
            # SMS
            cuoral_client = CuoralAPI()
            cuoral_client.send_sms(
                withdrawal.user.phone,
                f"Your withdrawal of NGN {withdrawal.amount} has been completed successfully."
            )

            # Email
            emailclient = MailClient()
            emailclient.send_email(
                to_email=withdrawal.user.email,
                subject="Withdrawal Successful",
                template_name="emails/withdrawal_success.html",
                context={
                    "amount": f"NGN {withdrawal.amount}",
                    "bank_name": withdrawal.bank_name,
                    "account_number": withdrawal.account_number
                },
                to_name=withdrawal.user.first_name
            )

            logger.info(f"Notified user {withdrawal.user.email} of successful withdrawal {withdrawal.id}")

        except Exception as e:
            logger.error(f"Failed to notify user {withdrawal.user.email}: {str(e)}")

    def _refund_user(self, withdrawal):
        """Refund user for failed withdrawal"""
        try:
            wallet = withdrawal.user.wallet
            wallet.deposit(Decimal(str(withdrawal.amount)))

            # Notify user
            cuoral_client = CuoralAPI()
            cuoral_client.send_sms(
                withdrawal.user.phone,
                f"Your withdrawal of NGN {withdrawal.amount} failed. Funds have been refunded to your wallet."
            )

            logger.info(f"Refunded user {withdrawal.user.email} for failed withdrawal {withdrawal.id}")

        except Exception as e:
            logger.error(f"Failed to refund user {withdrawal.user.email}: {str(e)}")
            raise

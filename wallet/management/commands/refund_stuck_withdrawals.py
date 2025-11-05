#!/usr/bin/env python
"""
Refund withdrawals that were created with the old code (before Embedly integration).
These withdrawals have status='pending' but no transaction_ref (never sent to Embedly).

Usage:
    python manage.py refund_stuck_withdrawals --dry-run  # Preview what will be refunded
    python manage.py refund_stuck_withdrawals             # Actually refund
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from wallet.models import WithdrawalRequest
from providers.helpers.cuoral import CuoralAPI
from notification.helper.email import MailClient

User = get_user_model()

import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refund stuck withdrawals from old code (no transaction_ref)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what will be refunded without actually refunding'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write('=' * 70)
        self.stdout.write('Refunding Stuck Withdrawals')
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No actual changes will be made'))
        self.stdout.write('=' * 70)

        # Find withdrawals that:
        # 1. Status is 'pending'
        # 2. No transaction_ref (never sent to Embedly)
        stuck_withdrawals = WithdrawalRequest.objects.filter(
            status='pending',
            transaction_ref__isnull=True
        ).order_by('created_at')

        if not stuck_withdrawals.exists():
            self.stdout.write(self.style.SUCCESS('✅ No stuck withdrawals found'))
            return

        self.stdout.write(f'\nFound {stuck_withdrawals.count()} stuck withdrawal(s):\n')

        # Display all stuck withdrawals
        total_amount = Decimal('0')
        for w in stuck_withdrawals:
            self.stdout.write(
                f"  ID: {w.id:4d} | User: {w.user.email:30s} | "
                f"Amount: NGN {w.amount:8.2f} | Bank: {w.bank_name:30s} | "
                f"Created: {w.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
            total_amount += w.amount

        self.stdout.write(f'\nTotal amount to refund: NGN {total_amount:.2f}')

        if dry_run:
            self.stdout.write('\n' + self.style.WARNING('DRY RUN - No changes made. Run without --dry-run to proceed.'))
            return

        # Confirm before proceeding
        self.stdout.write('\n' + self.style.WARNING('⚠️  This will refund all users and mark withdrawals as failed.'))
        confirm = input('Type "REFUND" to proceed: ')

        if confirm != 'REFUND':
            self.stdout.write(self.style.ERROR('❌ Aborted'))
            return

        # Process refunds
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('Processing Refunds...')
        self.stdout.write('=' * 70 + '\n')

        refunded_count = 0
        failed_count = 0

        for withdrawal in stuck_withdrawals:
            try:
                self.stdout.write(f'Processing #{withdrawal.id} for {withdrawal.user.email}...')

                # Get user's wallet
                wallet = withdrawal.user.wallet

                # Refund the amount
                wallet.deposit(Decimal(str(withdrawal.amount)))

                # Update withdrawal status
                withdrawal.status = 'failed'
                withdrawal.error_message = 'Withdrawal was stuck (never processed by old code). Refunded automatically.'
                withdrawal.save()

                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Refunded NGN {withdrawal.amount} to {withdrawal.user.email}')
                )

                # Send notification
                try:
                    self._notify_user(withdrawal)
                    self.stdout.write('  📧 Notification sent')
                except Exception as notif_error:
                    logger.error(f"Failed to notify user {withdrawal.user.email}: {notif_error}")
                    self.stdout.write(self.style.WARNING('  ⚠️  Notification failed (but refund successful)'))

                refunded_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Failed to refund: {str(e)}')
                )
                logger.error(f"Failed to refund withdrawal {withdrawal.id}: {str(e)}", exc_info=True)
                failed_count += 1

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(f'  Total found: {stuck_withdrawals.count()}')
        self.stdout.write(f'  Successfully refunded: {refunded_count}')
        self.stdout.write(f'  Failed: {failed_count}')
        self.stdout.write('=' * 70)

    def _notify_user(self, withdrawal):
        """Send notification to user about refund"""
        try:
            # SMS
            cuoral_client = CuoralAPI()
            cuoral_client.send_sms(
                withdrawal.user.phone,
                f"Your withdrawal of NGN {withdrawal.amount} was not processed due to a system issue. "
                f"The full amount has been refunded to your wallet. We apologize for the inconvenience."
            )

            # Email
            emailclient = MailClient()
            emailclient.send_email(
                to_email=withdrawal.user.email,
                subject="Withdrawal Refunded - System Issue",
                template_name="emails/withdrawal_refund.html",
                context={
                    "amount": f"NGN {withdrawal.amount}",
                    "bank_name": withdrawal.bank_name,
                    "account_number": withdrawal.account_number,
                    "reason": "Your withdrawal request was not processed due to a system issue. We have refunded the full amount to your wallet."
                },
                to_name=withdrawal.user.first_name
            )

            logger.info(f"Notified user {withdrawal.user.email} about refund for withdrawal {withdrawal.id}")

        except Exception as e:
            logger.error(f"Failed to notify user {withdrawal.user.email}: {str(e)}")
            raise

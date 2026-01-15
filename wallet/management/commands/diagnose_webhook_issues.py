"""
Django management command to diagnose webhook and deposit issues
Usage: python manage.py diagnose_webhook_issues
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from wallet.models import Wallet, WalletTransaction
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Diagnose why deposits are not being credited to wallets'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('WALLET DEPOSIT DIAGNOSTIC REPORT'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # 1. Check webhook configuration
        self.stdout.write(self.style.WARNING('1. WEBHOOK CONFIGURATION CHECK'))
        self.stdout.write('-' * 80)

        embedly_key = getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None)
        psb9_secret = getattr(settings, 'PSB9_CLIENT_SECRET', None)

        if embedly_key:
            self.stdout.write(self.style.SUCCESS(f'✓ EMBEDLY_API_KEY_PRODUCTION is set ({len(embedly_key)} chars)'))
        else:
            self.stdout.write(self.style.ERROR('✗ EMBEDLY_API_KEY_PRODUCTION is NOT set - Embedly webhooks will FAIL'))

        if psb9_secret:
            self.stdout.write(self.style.SUCCESS(f'✓ PSB9_CLIENT_SECRET is set ({len(psb9_secret)} chars)'))
        else:
            self.stdout.write(self.style.ERROR('✗ PSB9_CLIENT_SECRET is NOT set - 9PSB webhooks will FAIL'))

        self.stdout.write('')

        # 2. Check webhook URLs
        self.stdout.write(self.style.WARNING('2. WEBHOOK URLS'))
        self.stdout.write('-' * 80)
        base_url = getattr(settings, 'BASE_URL', 'https://your-domain.com')
        embedly_webhook_url = f"{base_url}/wallet/embedly/webhook/secure"
        psb9_webhook_url = f"{base_url}/wallet/9psb/webhook"

        self.stdout.write(f'Embedly webhook URL: {embedly_webhook_url}')
        self.stdout.write(f'9PSB webhook URL: {psb9_webhook_url}')
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Make sure these URLs are registered with your payment providers!'))
        self.stdout.write('')

        # 3. Check recent transactions
        self.stdout.write(self.style.WARNING('3. RECENT DEPOSIT ACTIVITY (Last 7 days)'))
        self.stdout.write('-' * 80)

        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_credits = WalletTransaction.objects.filter(
            transaction_type='credit',
            created_at__gte=seven_days_ago
        ).order_by('-created_at')

        credit_count = recent_credits.count()

        if credit_count == 0:
            self.stdout.write(self.style.ERROR(f'✗ NO DEPOSITS in the last 7 days - This indicates webhooks are NOT working!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ {credit_count} deposits recorded in the last 7 days'))

            # Show last 5 deposits
            self.stdout.write('')
            self.stdout.write('Last 5 deposits:')
            for txn in recent_credits[:5]:
                self.stdout.write(f'  • {txn.created_at.strftime("%Y-%m-%d %H:%M")} - '
                                f'{txn.wallet.user.email} - '
                                f'₦{txn.amount} - '
                                f'Ref: {txn.external_reference}')

        self.stdout.write('')

        # 4. Check wallet configurations
        self.stdout.write(self.style.WARNING('4. WALLET CONFIGURATION CHECK'))
        self.stdout.write('-' * 80)

        total_wallets = Wallet.objects.count()
        wallets_with_embedly = Wallet.objects.exclude(account_number__isnull=True).exclude(account_number='').count()
        wallets_with_9psb = Wallet.objects.exclude(psb9_account_number__isnull=True).exclude(psb9_account_number='').count()

        self.stdout.write(f'Total wallets: {total_wallets}')
        self.stdout.write(f'Wallets with Embedly account: {wallets_with_embedly}')
        self.stdout.write(f'Wallets with 9PSB account: {wallets_with_9psb}')

        if wallets_with_embedly == 0 and wallets_with_9psb == 0:
            self.stdout.write(self.style.ERROR('✗ NO wallets have virtual account numbers - Users cannot receive deposits!'))

        self.stdout.write('')

        # 5. Check for duplicate references (potential webhook replay issues)
        self.stdout.write(self.style.WARNING('5. DUPLICATE REFERENCE CHECK'))
        self.stdout.write('-' * 80)

        from django.db.models import Count
        duplicates = WalletTransaction.objects.values('external_reference').annotate(
            count=Count('id')
        ).filter(count__gt=1).exclude(external_reference__isnull=True)

        dup_count = duplicates.count()
        if dup_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Found {dup_count} duplicate references (webhook replays)'))
            for dup in duplicates[:5]:
                self.stdout.write(f'  • Ref: {dup["external_reference"]} - Count: {dup["count"]}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ No duplicate references found'))

        self.stdout.write('')

        # 6. Check for users with zero balance but transactions
        self.stdout.write(self.style.WARNING('6. BALANCE MISMATCH CHECK'))
        self.stdout.write('-' * 80)

        from django.db.models import Sum
        from decimal import Decimal

        problematic_wallets = []
        for wallet in Wallet.objects.all()[:100]:  # Check first 100 wallets
            credits = WalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='credit'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            debits = WalletTransaction.objects.filter(
                wallet=wallet,
                transaction_type='debit'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

            expected_balance = credits - debits
            actual_balance = wallet.balance

            if abs(expected_balance - actual_balance) > Decimal('0.01'):
                problematic_wallets.append({
                    'user': wallet.user.email,
                    'expected': expected_balance,
                    'actual': actual_balance,
                    'difference': expected_balance - actual_balance
                })

        if problematic_wallets:
            self.stdout.write(self.style.ERROR(f'✗ Found {len(problematic_wallets)} wallets with balance mismatches:'))
            for pw in problematic_wallets[:5]:
                self.stdout.write(f'  • {pw["user"]}: Expected ₦{pw["expected"]}, Actual ₦{pw["actual"]}, Diff: ₦{pw["difference"]}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ All checked wallets have correct balances'))

        self.stdout.write('')

        # 7. Summary and recommendations
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('RECOMMENDATIONS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        if credit_count == 0:
            self.stdout.write(self.style.ERROR('🚨 CRITICAL: NO DEPOSITS in the last 7 days!'))
            self.stdout.write('')
            self.stdout.write('Possible causes:')
            self.stdout.write('1. Webhook URLs not registered with payment providers')
            self.stdout.write('2. Webhook signature verification failing')
            self.stdout.write('3. Firewall blocking incoming webhooks')
            self.stdout.write('4. Payment provider having issues')
            self.stdout.write('')
            self.stdout.write('Action items:')
            self.stdout.write('• Check application logs for webhook errors')
            self.stdout.write('• Verify webhook URLs are registered with Embedly and 9PSB')
            self.stdout.write('• Test webhook endpoints manually')
            self.stdout.write('• Check if webhook secrets match provider configuration')
        else:
            self.stdout.write(self.style.SUCCESS('✓ Webhooks appear to be working (deposits are being recorded)'))
            self.stdout.write('')
            self.stdout.write('If users are still complaining:')
            self.stdout.write('• Ask which account number they sent money to')
            self.stdout.write('• Check if the transfer reference exists in WalletTransaction')
            self.stdout.write('• Verify the correct virtual account number was used')
            self.stdout.write('• Check if the user has both Embedly and 9PSB accounts configured')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('END OF DIAGNOSTIC REPORT'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

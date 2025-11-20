"""
Django management command to check webhook configuration.

Usage:
    python manage.py check_webhook_config
"""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Check webhook secret configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('WEBHOOK CONFIGURATION CHECK'))
        self.stdout.write(self.style.SUCCESS('='*70))

        # Check for webhook secrets
        secrets = {
            'EMBEDLY_WEBHOOK_SECRET': getattr(settings, 'EMBEDLY_WEBHOOK_SECRET', None),
            'EMBEDLY_WEBHOOK_KEY': getattr(settings, 'EMBEDLY_WEBHOOK_KEY', None),
            'EMBEDLY_API_KEY_PRODUCTION': getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None),
            'EMBEDLY_ORGANIZATION_ID_PRODUCTION': getattr(settings, 'EMBEDLY_ORGANIZATION_ID_PRODUCTION', None),
        }

        self.stdout.write('\nWebhook Secret Configuration:')
        self.stdout.write('-'*70)
        
        found_secrets = []
        for key, value in secrets.items():
            if value:
                # Show first and last 4 chars for security
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                self.stdout.write(self.style.SUCCESS(f"  ✓ {key}: {masked} (configured)"))
                found_secrets.append(key)
            else:
                self.stdout.write(self.style.WARNING(f"  ✗ {key}: Not configured"))

        if not found_secrets:
            self.stdout.write('\n' + self.style.ERROR('⚠️  NO WEBHOOK SECRETS CONFIGURED!'))
            self.stdout.write('\nTo fix this:')
            self.stdout.write('1. Get your webhook secret from Embedly dashboard')
            self.stdout.write('2. Set it in your environment variables:')
            self.stdout.write('   export EMBEDLY_WEBHOOK_SECRET=your_secret_here')
            self.stdout.write('3. Or add it to your .env file:')
            self.stdout.write('   EMBEDLY_WEBHOOK_SECRET=your_secret_here')
            self.stdout.write('4. Restart your server')
        else:
            self.stdout.write(f'\n✓ Found {len(found_secrets)} secret(s) configured')
            self.stdout.write('  The webhook handler will try these secrets in order.')

        # Check webhook URL
        self.stdout.write('\n' + '-'*70)
        self.stdout.write('Webhook URL Configuration:')
        self.stdout.write('-'*70)
        self.stdout.write('  Expected URL: https://app.gidinest.com/api/v1/wallet/embedly/webhook/secure')
        self.stdout.write('  Make sure this URL is configured in your Embedly dashboard')

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Check complete!'))
        self.stdout.write('='*70 + '\n')














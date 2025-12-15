"""
Diagnostic tool for Embedly webhook signature issues.

This command helps diagnose webhook signature verification problems by:
1. Checking configuration
2. Testing signature generation
3. Providing detailed diagnostics

Usage:
    python manage.py diagnose_webhook_signature
    python manage.py diagnose_webhook_signature --test-signature <signature> --test-body <json>
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import hmac
import hashlib
import json


class Command(BaseCommand):
    help = 'Diagnose Embedly webhook signature verification issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-signature',
            type=str,
            help='Test a specific signature value'
        )
        parser.add_argument(
            '--test-body',
            type=str,
            help='Test webhook body (JSON string)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('EMBEDLY WEBHOOK SIGNATURE DIAGNOSTIC'))
        self.stdout.write(self.style.SUCCESS('='*80))

        # Step 1: Check configuration
        self._check_configuration()

        # Step 2: Test signature generation
        self._test_signature_generation()

        # Step 3: If user provided test data, verify it
        if options['test_signature'] and options['test_body']:
            self._verify_test_signature(options['test_signature'], options['test_body'])

        # Step 4: Recommendations
        self._show_recommendations()

        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('Diagnostic complete!'))
        self.stdout.write('='*80 + '\n')

    def _check_configuration(self):
        """Check webhook secret configuration"""
        self.stdout.write('\n' + self.style.WARNING('Step 1: Configuration Check'))
        self.stdout.write('-'*80)

        secrets = {
            'EMBEDLY_WEBHOOK_SECRET': getattr(settings, 'EMBEDLY_WEBHOOK_SECRET', None),
            'EMBEDLY_WEBHOOK_KEY': getattr(settings, 'EMBEDLY_WEBHOOK_KEY', None),
            'EMBEDLY_API_KEY_PRODUCTION': getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None),
            'EMBEDLY_ORGANIZATION_ID_PRODUCTION': getattr(settings, 'EMBEDLY_ORGANIZATION_ID_PRODUCTION', None),
        }

        self.configured_secrets = []
        for key, value in secrets.items():
            if value:
                masked = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                self.stdout.write(self.style.SUCCESS(f"  ✓ {key}: {masked} (length: {len(value)})"))
                self.configured_secrets.append((key, value))
            else:
                self.stdout.write(self.style.ERROR(f"  ✗ {key}: NOT CONFIGURED"))

        if not self.configured_secrets:
            self.stdout.write('\n' + self.style.ERROR('  ⚠️  NO SECRETS CONFIGURED!'))
            self.stdout.write('  This will cause all webhook signatures to fail.')
        else:
            self.stdout.write(f'\n  Found {len(self.configured_secrets)} configured secret(s)')

    def _test_signature_generation(self):
        """Test signature generation with sample data"""
        self.stdout.write('\n' + self.style.WARNING('Step 2: Signature Generation Test'))
        self.stdout.write('-'*80)

        # Sample webhook payload
        test_payload = {
            "event": "nip",
            "data": {
                "accountNumber": "1234567890",
                "reference": "TEST_REF_123",
                "amount": 1000,
                "senderName": "Test Sender",
                "senderBank": "Test Bank"
            }
        }

        body_string = json.dumps(test_payload, separators=(',', ':'))
        self.stdout.write(f'\nTest payload (length: {len(body_string)} bytes):')
        self.stdout.write(json.dumps(test_payload, indent=2))

        if not self.configured_secrets:
            self.stdout.write('\n' + self.style.ERROR('Cannot generate signatures - no secrets configured'))
            return

        self.stdout.write('\n' + self.style.WARNING('Generated signatures:'))
        self.stdout.write('-'*80)

        for key_name, secret_value in self.configured_secrets:
            self.stdout.write(f'\nUsing secret: {key_name}')

            # Generate SHA256 signature
            sha256_sig = hmac.new(
                secret_value.encode('utf-8'),
                body_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            # Generate SHA512 signature
            sha512_sig = hmac.new(
                secret_value.encode('utf-8'),
                body_string.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()

            self.stdout.write(f'  SHA256: {sha256_sig}')
            self.stdout.write(f'  SHA512: {sha512_sig}')

    def _verify_test_signature(self, provided_sig, body_json):
        """Verify a provided signature against configured secrets"""
        self.stdout.write('\n' + self.style.WARNING('Step 3: Test Signature Verification'))
        self.stdout.write('-'*80)

        self.stdout.write(f'\nProvided signature: {provided_sig}')
        self.stdout.write(f'Body: {body_json[:100]}...')

        if not self.configured_secrets:
            self.stdout.write('\n' + self.style.ERROR('Cannot verify - no secrets configured'))
            return

        # Normalize signature (remove algorithm prefix if present)
        normalized_sig = provided_sig.split('=')[-1].split(':')[-1].strip().lower()

        matched = False
        for key_name, secret_value in self.configured_secrets:
            # Try SHA256
            sha256_sig = hmac.new(
                secret_value.encode('utf-8'),
                body_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest().lower()

            # Try SHA512
            sha512_sig = hmac.new(
                secret_value.encode('utf-8'),
                body_json.encode('utf-8'),
                hashlib.sha512
            ).hexdigest().lower()

            if hmac.compare_digest(sha256_sig, normalized_sig):
                self.stdout.write(self.style.SUCCESS(f'\n✓ MATCH with {key_name} using SHA256'))
                matched = True
            elif hmac.compare_digest(sha512_sig, normalized_sig):
                self.stdout.write(self.style.SUCCESS(f'\n✓ MATCH with {key_name} using SHA512'))
                matched = True

        if not matched:
            self.stdout.write(self.style.ERROR('\n✗ NO MATCH - Signature does not match any configured secret'))

    def _show_recommendations(self):
        """Show recommendations based on findings"""
        self.stdout.write('\n' + self.style.WARNING('Recommendations'))
        self.stdout.write('-'*80)

        if not self.configured_secrets:
            self.stdout.write(self.style.ERROR('\n1. ADD WEBHOOK SECRET'))
            self.stdout.write('   Add EMBEDLY_WEBHOOK_SECRET to your .env file:')
            self.stdout.write('   EMBEDLY_WEBHOOK_SECRET=your_secret_here')
            self.stdout.write('\n2. GET SECRET FROM EMBEDLY')
            self.stdout.write('   Contact Embedly support or check your dashboard')
            self.stdout.write('\n3. RESTART APPLICATION')
            self.stdout.write('   Restart Django to load the new configuration')
        else:
            primary_secret = getattr(settings, 'EMBEDLY_WEBHOOK_SECRET', None)
            if not primary_secret:
                self.stdout.write(self.style.WARNING('\n⚠️  EMBEDLY_WEBHOOK_SECRET not set'))
                self.stdout.write('   Currently using fallback secrets (API key or Org ID)')
                self.stdout.write('   This may work, but it\'s better to set the dedicated webhook secret')
            else:
                self.stdout.write(self.style.SUCCESS('\n✓ Configuration looks good!'))
                self.stdout.write('   If webhooks are still failing, check:')
                self.stdout.write('   1. Embedly is sending the correct signature header')
                self.stdout.write('   2. The webhook URL is correctly configured in Embedly dashboard')
                self.stdout.write('   3. Application logs for detailed error messages')

        self.stdout.write('\nFor more help, see: WEBHOOK_SIGNATURE_FIX.md')

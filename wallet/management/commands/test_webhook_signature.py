"""
Django management command to test webhook signature verification
Usage: python manage.py test_webhook_signature
"""
import json
import hashlib
import hmac
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Test webhook signature verification for Embedly and 9PSB'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('WEBHOOK SIGNATURE TEST'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')

        # Test payload (similar to what providers send)
        test_payload = {
            "event": "nip",
            "data": {
                "accountNumber": "1234567890",
                "reference": "TEST_REF_12345",
                "amount": 10000,
                "senderName": "Test User",
                "senderBank": "Test Bank"
            }
        }

        payload_json = json.dumps(test_payload)
        payload_bytes = payload_json.encode('utf-8')

        # Test Embedly signature
        self.stdout.write(self.style.WARNING('1. EMBEDLY SIGNATURE TEST'))
        self.stdout.write('-' * 80)

        embedly_key = getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None)

        if not embedly_key:
            self.stdout.write(self.style.ERROR('✗ EMBEDLY_API_KEY_PRODUCTION is NOT configured'))
        else:
            self.stdout.write(f'Secret length: {len(embedly_key)} characters')

            # Generate SHA-512 signature (Embedly's documented method)
            sha512_sig = hmac.new(
                embedly_key.encode('utf-8'),
                payload_bytes,
                hashlib.sha512
            ).hexdigest()

            # Generate SHA-256 signature (fallback)
            sha256_sig = hmac.new(
                embedly_key.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()

            self.stdout.write('')
            self.stdout.write('Expected signatures for test payload:')
            self.stdout.write(f'SHA-512: {sha512_sig}')
            self.stdout.write(f'SHA-256: {sha256_sig}')
            self.stdout.write('')
            self.stdout.write('Send these to Embedly support if signatures are not matching!')

        self.stdout.write('')

        # Test 9PSB signature
        self.stdout.write(self.style.WARNING('2. 9PSB SIGNATURE TEST'))
        self.stdout.write('-' * 80)

        psb9_secret = getattr(settings, 'PSB9_CLIENT_SECRET', None)

        if not psb9_secret:
            self.stdout.write(self.style.ERROR('✗ PSB9_CLIENT_SECRET is NOT configured'))
        else:
            self.stdout.write(f'Secret length: {len(psb9_secret)} characters')

            # Generate HMAC-SHA256 signature (9PSB's method)
            psb9_sig = hmac.new(
                psb9_secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()

            self.stdout.write('')
            self.stdout.write('Expected signature for test payload:')
            self.stdout.write(f'HMAC-SHA256: {psb9_sig}')
            self.stdout.write('')
            self.stdout.write('Send this to 9PSB support if signatures are not matching!')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('HOW TO USE THIS'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write('')
        self.stdout.write('1. Ask your payment provider to send a test webhook')
        self.stdout.write('2. Copy the X-Auth-Signature header from the failed request')
        self.stdout.write('3. Compare it with the signatures above')
        self.stdout.write('4. If they do not match:')
        self.stdout.write('   • Verify the webhook secret is correct')
        self.stdout.write('   • Check if the provider changed their signature algorithm')
        self.stdout.write('   • Ensure the payload format matches what they send')
        self.stdout.write('')

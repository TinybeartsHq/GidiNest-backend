"""
Test script to verify webhook endpoint is accessible and working.

Usage:
    python manage.py test_webhook_endpoint
"""
from django.core.management.base import BaseCommand
import requests
import json
import hmac
import hashlib
from django.conf import settings


class Command(BaseCommand):
    help = 'Test webhook endpoint accessibility'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('WEBHOOK ENDPOINT TEST'))
        self.stdout.write(self.style.SUCCESS('='*70))

        # Get API key
        api_key = getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None)
        if not api_key:
            self.stdout.write(self.style.ERROR('EMBEDLY_API_KEY_PRODUCTION not configured'))
            return

        # Test payload
        test_payload = {
            "event": "nip",
            "data": {
                "accountNumber": "9710239954",
                "reference": "TEST_REF_12345",
                "amount": 100,
                "senderName": "Test Sender",
                "senderBank": "Test Bank"
            }
        }

        # Create signature
        body_string = json.dumps(test_payload, separators=(',', ':'))
        signature = hmac.new(
            api_key.encode('utf-8'),
            body_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        self.stdout.write(f'\nTest Payload:')
        self.stdout.write(json.dumps(test_payload, indent=2))
        self.stdout.write(f'\nComputed Signature: {signature[:60]}...')
        self.stdout.write(f'API Key: {api_key[:10]}...{api_key[-4:]}')

        # Test local endpoint
        self.stdout.write('\n' + '-'*70)
        self.stdout.write('Testing LOCAL endpoint (127.0.0.1)')
        self.stdout.write('-'*70)
        
        try:
            response = requests.post(
                'http://127.0.0.1:8000/api/v1/wallet/embedly/webhook/secure',
                json=test_payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-embedly-signature': signature
                },
                timeout=5
            )
            self.stdout.write(f'Status: {response.status_code}')
            self.stdout.write(f'Response: {response.text[:200]}')
        except requests.exceptions.ConnectionError:
            self.stdout.write(self.style.WARNING('  ✗ Cannot connect - is Django running locally?'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))

        # Test production endpoint
        self.stdout.write('\n' + '-'*70)
        self.stdout.write('Testing PRODUCTION endpoint (app.gidinest.com)')
        self.stdout.write('-'*70)
        
        try:
            response = requests.post(
                'https://app.gidinest.com/api/v1/wallet/embedly/webhook/secure',
                json=test_payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-embedly-signature': signature
                },
                timeout=10
            )
            self.stdout.write(f'Status: {response.status_code}')
            self.stdout.write(f'Response: {response.text[:200]}')
            
            if response.status_code == 200:
                self.stdout.write(self.style.SUCCESS('  ✓ Endpoint is accessible!'))
            elif response.status_code == 403:
                self.stdout.write(self.style.WARNING('  ⚠️  Endpoint accessible but signature verification failed'))
            else:
                self.stdout.write(self.style.ERROR(f'  ✗ Unexpected status: {response.status_code}'))
        except requests.exceptions.SSLError:
            self.stdout.write(self.style.ERROR('  ✗ SSL Error - check certificate'))
        except requests.exceptions.Timeout:
            self.stdout.write(self.style.ERROR('  ✗ Timeout - endpoint not responding'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('Test complete!'))
        self.stdout.write('='*70 + '\n')







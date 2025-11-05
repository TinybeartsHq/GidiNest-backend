"""
Django management command to test Embedly API connection and configuration.

Usage:
    python manage.py test_embedly_connection
    python manage.py test_embedly_connection --customer-id <id>
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from providers.helpers.embedly import EmbedlyClient
from account.models.users import UserModel


class Command(BaseCommand):
    help = 'Test Embedly API connection and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customer-id',
            type=str,
            help='Test with a specific customer ID',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('EMBEDLY API CONNECTION TEST'))
        self.stdout.write(self.style.SUCCESS('='*60))

        # Check configuration
        self.stdout.write('\n1. Checking Configuration...')

        api_key = getattr(settings, 'EMBEDLY_API_KEY_PRODUCTION', None)
        org_id = getattr(settings, 'EMBEDLY_ORGANIZATION_ID_PRODUCTION', None)

        if not api_key or api_key == 'your_embedly_prod_key':
            self.stdout.write(self.style.ERROR('   ✗ API Key not configured properly'))
            self.stdout.write(self.style.WARNING('   Please set EMBEDLY_API_KEY_PRODUCTION in your .env file'))
            return
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✓ API Key configured: {api_key[:10]}...'))

        if not org_id or org_id == 'your_org_id':
            self.stdout.write(self.style.ERROR('   ✗ Organization ID not configured properly'))
            self.stdout.write(self.style.WARNING('   Please set EMBEDLY_ORGANIZATION_ID_PRODUCTION in your .env file'))
            return
        else:
            self.stdout.write(self.style.SUCCESS(f'   ✓ Organization ID configured: {org_id[:10]}...'))

        # Initialize client
        self.stdout.write('\n2. Initializing Embedly Client...')
        try:
            client = EmbedlyClient()
            self.stdout.write(self.style.SUCCESS(f'   ✓ Client initialized'))
            self.stdout.write(f'   Base URL: {client.base_url}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Failed to initialize client: {str(e)}'))
            return

        # Test with a real customer ID
        self.stdout.write('\n3. Testing API Call...')

        customer_id = options.get('customer_id')

        if not customer_id:
            # Find a user with embedly_customer_id
            user = UserModel.objects.exclude(
                embedly_customer_id=""
            ).exclude(
                embedly_customer_id__isnull=True
            ).first()

            if user:
                customer_id = user.embedly_customer_id
                self.stdout.write(f'   Using customer ID from user {user.email}')
            else:
                self.stdout.write(self.style.WARNING('   No users with embedly_customer_id found'))
                self.stdout.write(self.style.WARNING('   Run with --customer-id <id> to test with a specific ID'))
                return

        self.stdout.write(f'   Testing with customer ID: {customer_id[:20]}...')

        try:
            response = client.get_customer(customer_id)

            if response.get('success'):
                self.stdout.write(self.style.SUCCESS('   ✓ API call successful!'))

                data = response.get('data', {})
                self.stdout.write('\n   Customer Data Retrieved:')
                self.stdout.write(f"   - KYC Level: {data.get('kycLevel', 'N/A')}")
                self.stdout.write(f"   - Has Wallet: {data.get('hasWallet', False)}")
                self.stdout.write(f"   - Wallets: {len(data.get('wallets', []))}")

                if data.get('wallets'):
                    wallet = data['wallets'][0]
                    va = wallet.get('virtualAccount', {})
                    self.stdout.write(f"   - First Wallet Account: {va.get('accountNumber', 'N/A')}")

            else:
                self.stdout.write(self.style.ERROR('   ✗ API call failed'))
                self.stdout.write(f"   Error Message: {response.get('message', 'Unknown')}")
                self.stdout.write(f"   Error Code: {response.get('code', 'N/A')}")

                error_data = response.get('data', {})
                if error_data:
                    self.stdout.write(f"   Error Details: {error_data}")

                # Common issues and solutions
                self.stdout.write('\n   Possible Issues:')
                self.stdout.write('   1. Invalid or expired API key')
                self.stdout.write('   2. Customer ID not found in Embedly')
                self.stdout.write('   3. Network connectivity issues')
                self.stdout.write('   4. Embedly API is down or rate-limited')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ✗ Exception occurred: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

        self.stdout.write('\n' + '='*60)
        self.stdout.write('Test completed')
        self.stdout.write('='*60)

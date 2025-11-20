from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from account.models import UserModel, UserDevices, UserSession, UserBankAccount, CustomerNote
from wallet.models import Wallet, WalletTransaction, WithdrawalRequest, PaymentLink, PaymentLinkContribution
from savings.models import SavingsGoalModel, SavingsGoalTransaction
from core.models import ServerLog
from providers.models import ProviderRequestLog


class Command(BaseCommand):
    help = 'Set up customer support groups with appropriate permissions'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Setting up customer support groups...'))

        # Create the three support groups
        support_agent, _ = Group.objects.get_or_create(name='Support Agent')
        senior_support, _ = Group.objects.get_or_create(name='Senior Support')
        support_manager, _ = Group.objects.get_or_create(name='Support Manager')

        self.stdout.write(self.style.SUCCESS('✓ Created support groups'))

        # Clear existing permissions
        support_agent.permissions.clear()
        senior_support.permissions.clear()
        support_manager.permissions.clear()

        # Get content types for all models
        user_ct = ContentType.objects.get_for_model(UserModel)
        device_ct = ContentType.objects.get_for_model(UserDevices)
        session_ct = ContentType.objects.get_for_model(UserSession)
        bank_account_ct = ContentType.objects.get_for_model(UserBankAccount)
        note_ct = ContentType.objects.get_for_model(CustomerNote)
        wallet_ct = ContentType.objects.get_for_model(Wallet)
        transaction_ct = ContentType.objects.get_for_model(WalletTransaction)
        withdrawal_ct = ContentType.objects.get_for_model(WithdrawalRequest)
        payment_link_ct = ContentType.objects.get_for_model(PaymentLink)
        contribution_ct = ContentType.objects.get_for_model(PaymentLinkContribution)
        savings_goal_ct = ContentType.objects.get_for_model(SavingsGoalModel)
        savings_transaction_ct = ContentType.objects.get_for_model(SavingsGoalTransaction)
        server_log_ct = ContentType.objects.get_for_model(ServerLog)
        provider_log_ct = ContentType.objects.get_for_model(ProviderRequestLog)

        # ============================================
        # LEVEL 1: SUPPORT AGENT (Read-Only)
        # ============================================
        self.stdout.write(self.style.WARNING('\nConfiguring Support Agent permissions...'))

        agent_permissions = [
            # View users (limited fields, no sensitive data)
            Permission.objects.get(codename='view_usermodel', content_type=user_ct),

            # View devices
            Permission.objects.get(codename='view_userdevices', content_type=device_ct),

            # View wallets and transactions (read-only)
            Permission.objects.get(codename='view_wallet', content_type=wallet_ct),
            Permission.objects.get(codename='view_wallettransaction', content_type=transaction_ct),
            Permission.objects.get(codename='view_withdrawalrequest', content_type=withdrawal_ct),

            # View payment links
            Permission.objects.get(codename='view_paymentlink', content_type=payment_link_ct),
            Permission.objects.get(codename='view_paymentlinkcontribution', content_type=contribution_ct),

            # View savings
            Permission.objects.get(codename='view_savingsgoalmodel', content_type=savings_goal_ct),
            Permission.objects.get(codename='view_savingsgoaltransaction', content_type=savings_transaction_ct),

            # View and create customer notes
            Permission.objects.get(codename='view_customernote', content_type=note_ct),
            Permission.objects.get(codename='add_customernote', content_type=note_ct),
            Permission.objects.get(codename='change_customernote', content_type=note_ct),

            # View logs for debugging
            Permission.objects.get(codename='view_serverlog', content_type=server_log_ct),
            Permission.objects.get(codename='view_providerrequestlog', content_type=provider_log_ct),
        ]

        support_agent.permissions.set(agent_permissions)
        self.stdout.write(self.style.SUCCESS(f'✓ Added {len(agent_permissions)} permissions to Support Agent'))

        # ============================================
        # LEVEL 2: SENIOR SUPPORT (Limited Actions)
        # ============================================
        self.stdout.write(self.style.WARNING('\nConfiguring Senior Support permissions...'))

        senior_permissions = agent_permissions + [
            # Change users (for verification, PIN resets)
            Permission.objects.get(codename='change_usermodel', content_type=user_ct),

            # View sessions
            Permission.objects.get(codename='view_usersession', content_type=session_ct),

            # View and manage bank accounts
            Permission.objects.get(codename='view_userbankaccount', content_type=bank_account_ct),
            Permission.objects.get(codename='change_userbankaccount', content_type=bank_account_ct),

            # Delete customer notes (for cleanup)
            Permission.objects.get(codename='delete_customernote', content_type=note_ct),
        ]

        senior_support.permissions.set(senior_permissions)
        self.stdout.write(self.style.SUCCESS(f'✓ Added {len(senior_permissions)} permissions to Senior Support'))

        # ============================================
        # LEVEL 3: SUPPORT MANAGER (Full Access)
        # ============================================
        self.stdout.write(self.style.WARNING('\nConfiguring Support Manager permissions...'))

        manager_permissions = senior_permissions + [
            # Full user management (except delete)
            # Already has view and change from senior level

            # Manage sessions (remote logout)
            Permission.objects.get(codename='change_usersession', content_type=session_ct),
            Permission.objects.get(codename='delete_usersession', content_type=session_ct),

            # Manage devices
            Permission.objects.get(codename='change_userdevices', content_type=device_ct),
            Permission.objects.get(codename='delete_userdevices', content_type=device_ct),

            # Add/manage bank accounts
            Permission.objects.get(codename='add_userbankaccount', content_type=bank_account_ct),
            Permission.objects.get(codename='delete_userbankaccount', content_type=bank_account_ct),

            # Change withdrawal requests (for manual processing)
            Permission.objects.get(codename='change_withdrawalrequest', content_type=withdrawal_ct),

            # Change payment links (for disabling/enabling)
            Permission.objects.get(codename='change_paymentlink', content_type=payment_link_ct),

            # Change savings goals (for corrections)
            Permission.objects.get(codename='change_savingsgoalmodel', content_type=savings_goal_ct),
        ]

        support_manager.permissions.set(manager_permissions)
        self.stdout.write(self.style.SUCCESS(f'✓ Added {len(manager_permissions)} permissions to Support Manager'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('CUSTOMER SUPPORT GROUPS CONFIGURED SUCCESSFULLY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('\n📊 Summary:'))
        self.stdout.write(f'  • Support Agent: {support_agent.permissions.count()} permissions (read-only)')
        self.stdout.write(f'  • Senior Support: {senior_support.permissions.count()} permissions (limited actions)')
        self.stdout.write(f'  • Support Manager: {support_manager.permissions.count()} permissions (full support access)')

        self.stdout.write(self.style.WARNING('\n📝 Next Steps:'))
        self.stdout.write('  1. Create support staff users in Django admin')
        self.stdout.write('  2. Mark them as "Staff status" (is_staff=True)')
        self.stdout.write('  3. Assign them to appropriate support groups')
        self.stdout.write('  4. DO NOT mark as "Superuser status" unless needed')
        self.stdout.write(self.style.SUCCESS('\n✓ Done!\n'))

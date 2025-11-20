from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from account.models.users import UserModel
import getpass


class Command(BaseCommand):
    help = 'Create a staff user for admin access without requiring customer fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the staff user',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the staff user',
        )
        parser.add_argument(
            '--first-name',
            type=str,
            help='First name of the staff user',
        )
        parser.add_argument(
            '--last-name',
            type=str,
            help='Last name of the staff user',
        )
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Make this user an admin (superuser)',
        )
        parser.add_argument(
            '--non-interactive',
            action='store_true',
            help='Run in non-interactive mode (requires all arguments)',
        )

    def handle(self, *args, **options):
        # Determine if we're in interactive or non-interactive mode
        non_interactive = options.get('non_interactive', False)

        # Get email
        email = options.get('email')
        if not email:
            if non_interactive:
                raise CommandError('Email is required in non-interactive mode')
            email = input('Email address: ').strip()

        if not email:
            raise CommandError('Email address is required')

        # Check if user already exists
        if UserModel.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        # Get password
        password = options.get('password')
        if not password:
            if non_interactive:
                raise CommandError('Password is required in non-interactive mode')
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                raise CommandError('Passwords do not match')

        if not password:
            raise CommandError('Password is required')

        # Get first name
        first_name = options.get('first_name')
        if not first_name:
            if non_interactive:
                first_name = ''
            else:
                first_name = input('First name (optional): ').strip()

        # Get last name
        last_name = options.get('last_name')
        if not last_name:
            if non_interactive:
                last_name = ''
            else:
                last_name = input('Last name (optional): ').strip()

        # Determine role
        is_admin = options.get('admin', False)
        if not non_interactive and not is_admin:
            admin_response = input('Make this user an admin (superuser)? [y/N]: ').strip().lower()
            is_admin = admin_response == 'y'

        # Create the user
        try:
            with transaction.atomic():
                user = UserModel.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    username=email.split('@')[0],
                    is_staff=True,
                    is_superuser=is_admin,
                    is_active=True,
                    is_verified=True,
                    email_verified=True,
                    account_tier='Staff',
                    phone='',  # Not required for staff
                )
                user.set_password(password)
                user.save()

                self.stdout.write(self.style.SUCCESS(
                    f'\n✓ Staff user created successfully!\n'
                ))
                self.stdout.write(f'  Email: {email}')
                self.stdout.write(f'  Name: {first_name} {last_name}'.strip())
                self.stdout.write(f'  Role: {"Admin (Superuser)" if is_admin else "Staff"}')
                self.stdout.write(f'  Status: Active')
                self.stdout.write(f'\n  They can now login at: /internal-admin/\n')

        except Exception as e:
            raise CommandError(f'Error creating staff user: {str(e)}')

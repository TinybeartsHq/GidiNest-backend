"""
Django management command to sync user verification status from Embedly.

Usage:
    python manage.py sync_embedly_verifications                    # Sync all users
    python manage.py sync_embedly_verifications --limit 100        # Sync first 100 users
    python manage.py sync_embedly_verifications --emails user1@example.com user2@example.com
"""
from django.core.management.base import BaseCommand, CommandError
from account.services.sync_embedly import EmbedlySyncService
import json


class Command(BaseCommand):
    help = 'Sync user verification status from Embedly to local database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of users to sync',
        )
        parser.add_argument(
            '--emails',
            nargs='+',
            help='Sync specific users by email addresses',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed results for each user',
        )

    def handle(self, *args, **options):
        sync_service = EmbedlySyncService()

        self.stdout.write(self.style.SUCCESS('Starting Embedly verification sync...'))

        # Sync specific users by email
        if options['emails']:
            self.stdout.write(f"Syncing {len(options['emails'])} specific users...")
            results = sync_service.sync_users_by_email(options['emails'])
        # Sync all users (with optional limit)
        else:
            limit = options.get('limit')
            if limit:
                self.stdout.write(f"Syncing up to {limit} users...")
            else:
                self.stdout.write("Syncing all users with Embedly accounts...")
            results = sync_service.sync_all_users(limit=limit)

        # Display summary
        self.stdout.write(self.style.SUCCESS('\n=== Sync Summary ==='))
        self.stdout.write(f"Total users: {results['total_users']}")
        self.stdout.write(self.style.SUCCESS(f"Successful: {results['successful']}"))
        self.stdout.write(self.style.ERROR(f"Failed: {results['failed']}"))
        self.stdout.write(self.style.WARNING(f"Updated: {results['updated']}"))
        self.stdout.write(f"No changes: {results.get('no_changes', 0)}")

        # Show detailed results if verbose
        if options['verbose'] and results['details']:
            self.stdout.write(self.style.SUCCESS('\n=== Detailed Results ==='))
            for detail in results['details']:
                if detail['success']:
                    if detail.get('updated'):
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ {detail['email']}: {', '.join(detail['changes'])}"
                            )
                        )
                    else:
                        self.stdout.write(f"  {detail['email']}: No changes")
                else:
                    error_msg = detail.get('message', 'Unknown error')
                    error_details = detail.get('error_details', {})
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ {detail['email']}: {error_msg}"
                        )
                    )
                    if error_details and isinstance(error_details, dict):
                        # Show additional error context if available
                        if 'message' in error_details:
                            self.stdout.write(f"    Details: {error_details.get('message')}")
                        if 'error' in error_details:
                            self.stdout.write(f"    Error: {error_details.get('error')}")

        # Exit with error code if any syncs failed
        if results['failed'] > 0:
            raise CommandError(f"{results['failed']} user sync(s) failed")

        self.stdout.write(self.style.SUCCESS('\nSync completed successfully!'))

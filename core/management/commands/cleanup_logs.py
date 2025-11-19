from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import ServerLog


class Command(BaseCommand):
    help = 'Clean up old server logs from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete logs older than specified days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=days)
        old_logs = ServerLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} logs older than {days} days (before {cutoff_date})'
                )
            )
        else:
            old_logs.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {count} logs older than {days} days'
                )
            )

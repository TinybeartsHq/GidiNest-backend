from django.core.management.base import BaseCommand
from django.utils import timezone
from onboarding.models import PasswordResetOTP


class Command(BaseCommand):
    help = 'Cleanup expired and used password reset OTPs older than 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Delete OTPs older than this many days (default: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timezone.timedelta(days=days)

        # Find old OTPs to clean up
        old_otps = PasswordResetOTP.objects.filter(created_at__lt=cutoff_date)

        total_count = old_otps.count()
        used_count = old_otps.filter(is_used=True).count()
        expired_count = 0

        # Count expired OTPs
        for otp in old_otps:
            if otp.has_expired():
                expired_count += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {total_count} OTP records older than {days} day(s):'
                )
            )
            self.stdout.write(f'  - {used_count} used OTPs')
            self.stdout.write(f'  - {expired_count} expired OTPs')
            self.stdout.write(f'  - {total_count - used_count - expired_count} other OTPs')
        else:
            deleted_count, _ = old_otps.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} OTP records older than {days} day(s)'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'  - {used_count} used OTPs\n'
                    f'  - {expired_count} expired OTPs\n'
                    f'  - {deleted_count - used_count - expired_count} other OTPs'
                )
            )

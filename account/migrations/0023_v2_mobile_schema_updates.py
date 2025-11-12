# Generated manually for V2 Mobile schema updates
# Date: 2025-11-06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_usermodel_transaction_pin_usermodel_transaction_pin_set'),
    ]

    operations = [
        # UserModel V2 Fields - OAuth
        migrations.AddField(
            model_name='usermodel',
            name='apple_id',
            field=models.CharField(blank=True, default='', help_text='Apple User ID for Apple Sign In', max_length=200, null=True),
        ),
        
        # UserModel V2 Fields - Passcode Authentication
        migrations.AddField(
            model_name='usermodel',
            name='passcode_hash',
            field=models.CharField(blank=True, help_text='Hashed 6-digit passcode for quick login', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='passcode_set',
            field=models.BooleanField(default=False, help_text='Whether user has set a passcode'),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='biometric_enabled',
            field=models.BooleanField(default=False, help_text='Whether biometric authentication is enabled'),
        ),
        
        # UserModel V2 Fields - Transaction Limits & Restrictions
        migrations.AddField(
            model_name='usermodel',
            name='daily_limit',
            field=models.BigIntegerField(default=10000000, help_text='Daily transaction limit in kobo (default: ₦100,000)'),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='per_transaction_limit',
            field=models.BigIntegerField(default=5000000, help_text='Per transaction limit in kobo (default: ₦50,000)'),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='monthly_limit',
            field=models.BigIntegerField(default=100000000, help_text='Monthly transaction limit in kobo (default: ₦1,000,000)'),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='limit_restricted_until',
            field=models.DateTimeField(blank=True, help_text='Timestamp until which transaction limits are restricted', null=True),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='restricted_limit',
            field=models.BigIntegerField(blank=True, help_text='Restricted transaction limit in kobo during restriction period', null=True),
        ),
        
        # UserModel V2 Fields - Enhanced Verification
        migrations.AddField(
            model_name='usermodel',
            name='verification_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending', help_text='Overall KYC verification status', max_length=20),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='email_verified_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when email was verified', null=True),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='phone_verified_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when phone was verified', null=True),
        ),
        
        # UserModel V2 Fields - Soft Delete & Security
        migrations.AddField(
            model_name='usermodel',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when user was soft deleted', null=True),
        ),
        migrations.AddField(
            model_name='usermodel',
            name='last_login_at',
            field=models.DateTimeField(blank=True, help_text='Last login timestamp (more precise than last_login)', null=True),
        ),
        
        # UserSession Model
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('device_name', models.CharField(help_text="Device name (e.g., 'iPhone 14 Pro')", max_length=255)),
                ('device_type', models.CharField(choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web'), ('unknown', 'Unknown')], default='unknown', help_text='Device platform', max_length=50)),
                ('device_id', models.CharField(help_text='Unique device identifier', max_length=255)),
                ('ip_address', models.GenericIPAddressField(blank=True, help_text='IP address of the session', null=True)),
                ('location', models.CharField(blank=True, help_text="Approximate location (e.g., 'Lagos, Nigeria')", max_length=255, null=True)),
                ('refresh_token_hash', models.CharField(help_text='Hashed refresh token for invalidation', max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=True, help_text='Whether session is still valid')),
                ('expires_at', models.DateTimeField(help_text='When the refresh token expires')),
                ('last_active_at', models.DateTimeField(auto_now=True, help_text='Last time this session was used')),
                ('user', models.ForeignKey(help_text='User who owns this session', on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Session',
                'verbose_name_plural': 'User Sessions',
                'db_table': 'user_sessions',
                'ordering': ['-last_active_at'],
            },
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['user', 'is_active'], name='user_sessio_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['refresh_token_hash'], name='user_sessio_refresh__idx'),
        ),
        migrations.AddIndex(
            model_name='usersession',
            index=models.Index(fields=['device_id'], name='user_sessio_device__idx'),
        ),
        
        # UserBankAccount Model
        migrations.CreateModel(
            name='UserBankAccount',
            fields=[
                ('id', models.UUIDField(editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bank_name', models.CharField(help_text="Name of the bank (e.g., 'Access Bank')", max_length=100)),
                ('bank_code', models.CharField(help_text='Bank code for Nigeria (e.g., \'044\')', max_length=10)),
                ('account_number', models.CharField(help_text='Bank account number', max_length=20)),
                ('account_name', models.CharField(help_text='Account holder name (verified via bank)', max_length=255)),
                ('is_verified', models.BooleanField(default=False, help_text='Whether account has been verified via Embedly')),
                ('verified_at', models.DateTimeField(blank=True, help_text='When account was verified', null=True)),
                ('is_default', models.BooleanField(default=False, help_text='Whether this is the default account for withdrawals')),
                ('user', models.ForeignKey(help_text='User who owns this bank account', on_delete=django.db.models.deletion.CASCADE, related_name='bank_accounts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Bank Account',
                'verbose_name_plural': 'User Bank Accounts',
                'db_table': 'user_bank_accounts',
                'ordering': ['-is_default', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='userbankaccount',
            index=models.Index(fields=['user', 'is_default'], name='user_bank_a_user_id_idx'),
        ),
        migrations.AddIndex(
            model_name='userbankaccount',
            index=models.Index(fields=['account_number', 'bank_code'], name='user_bank_a_account_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='userbankaccount',
            unique_together={('user', 'account_number', 'bank_code')},
        ),
    ]




from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from core.helpers.model import BaseModel
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.hashers import make_password, check_password

class UserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra_fields):
        if not email:
            raise ValueError("Please provide email")

        email = self.normalize_email(email)
        user = self.model(email=email,**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user    

    def create_superuser(self,email,password,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        extra_fields.setdefault('is_active',True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("super user must have staff user")

        return self.create_user(email,password,**extra_fields)    

class UserModel(BaseModel, AbstractBaseUser,PermissionsMixin):
    """
        User model for user management and access restrictions
    """

    class Meta:
        db_table = 'users'
 

    username = models.CharField(null=True, blank=True, max_length=200)
    first_name = models.CharField(null=True, blank=True, max_length=200)
    last_name = models.CharField(null=True, blank=True, max_length=200)
    email = models.EmailField(null=False, unique=True)
    phone = models.CharField(null=True, blank=True, max_length=20)
    address = models.CharField(null=True, blank=True, max_length=200, default="")
    country = models.CharField(null=True, blank=True, max_length=200, default="")
    currency = models.CharField(null=True, blank=True, max_length=200, default="USD")
    dob = models.CharField(null=True, blank=True, max_length=200, default="")
    state = models.CharField(null=True, blank=True, max_length=200, default="")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Can access admin
    is_superuser = models.BooleanField(default=False)  # Superuser status
    password = models.CharField(max_length=200)
    last_login = models.DateTimeField(blank=True, null=True)
    google_id = models.CharField(null=True, max_length=200,default="")
    apple_id = models.CharField(null=True, max_length=200,default="", help_text="Apple User ID for Apple Sign In")
    bvn = models.CharField(null=True, max_length=12,default="")
    bvn_first_name = models.CharField(null=True, max_length=200,default="")
    bvn_last_name = models.CharField(null=True, max_length=200,default="")
    bvn_phone = models.CharField(null=True, max_length=200,default="")
    bvn_dob = models.CharField(null=True, max_length=200,default="")
    bvn_gender = models.CharField(null=True, max_length=200,default="")
    bvn_marital_status = models.CharField(null=True, max_length=200,default="")
    bvn_nationality = models.CharField(null=True, max_length=200,default="")
    bvn_residential_address = models.CharField(null=True, max_length=255,default="")
    bvn_state_of_residence = models.CharField(null=True, max_length=200,default="")
    bvn_watch_listed= models.CharField(null=True, max_length=200,default="")
    bvn_enrollment_bank= models.CharField(null=True, max_length=200,default="")


    has_bvn = models.BooleanField(default=False)

    # NIN-related fields
    nin = models.CharField(null=True, max_length=11, default="")
    nin_first_name = models.CharField(null=True, max_length=200, default="")
    nin_last_name = models.CharField(null=True, max_length=200, default="")
    nin_phone = models.CharField(null=True, max_length=200, default="")
    nin_dob = models.CharField(null=True, max_length=200, default="")
    nin_gender = models.CharField(null=True, max_length=200, default="")
    nin_marital_status = models.CharField(null=True, max_length=200, default="")
    nin_nationality = models.CharField(null=True, max_length=200, default="")
    nin_residential_address = models.CharField(null=True, max_length=255, default="")
    nin_state_of_residence = models.CharField(null=True, max_length=200, default="")
    has_nin = models.BooleanField(default=False)
    image = models.TextField(null=True, blank=True)
    account_tier = models.CharField(null=True, max_length=200,default="Tier 1")
    embedly_customer_id = models.CharField(null=True, max_length=200,default="")
    embedly_wallet_id = models.CharField(null=True, max_length=200,default="")
    has_virtual_wallet = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when email was verified")
    phone_verified_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when phone was verified")

    # Nudge tracking
    nudge_wallet_setup_sent = models.BooleanField(default=False, help_text="Whether wallet setup nudge has been sent")

    # V2 Mobile - Passcode Authentication (6-digit)
    passcode_hash = models.CharField(null=True, blank=True, max_length=255, help_text="Hashed 6-digit passcode for quick login")
    passcode_set = models.BooleanField(default=False, help_text="Whether user has set a passcode")
    biometric_enabled = models.BooleanField(default=False, help_text="Whether biometric authentication is enabled")

    # V2 Mobile - Transaction Limits & Restrictions
    daily_limit = models.BigIntegerField(default=10000000, help_text="Daily transaction limit in kobo (default: ₦100,000)")
    per_transaction_limit = models.BigIntegerField(default=5000000, help_text="Per transaction limit in kobo (default: ₦50,000)")
    monthly_limit = models.BigIntegerField(default=100000000, help_text="Monthly transaction limit in kobo (default: ₦1,000,000)")
    limit_restricted_until = models.DateTimeField(null=True, blank=True, help_text="Timestamp until which transaction limits are restricted")
    restricted_limit = models.BigIntegerField(null=True, blank=True, help_text="Restricted transaction limit in kobo during restriction period")

    # V2 Mobile - Enhanced Verification
    verification_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected')
        ],
        default='pending',
        help_text="Overall KYC verification status"
    )

    # Transaction PIN (existing, kept for backwards compatibility)
    transaction_pin = models.CharField(null=True, max_length=200, help_text="Hashed transaction PIN for withdrawals")
    transaction_pin_set = models.BooleanField(default=False, help_text="Whether user has set a transaction PIN")

    # Soft Delete Support
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when user was soft deleted")
    last_login_at = models.DateTimeField(null=True, blank=True, help_text="Last login timestamp (more precise than last_login)")
 

    indexes = [
        models.Index(fields=["email"])
    ]
  
    USERNAME_FIELD = "email"

    objects = UserManager()


    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-created_at']

 
 
 
    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    @classmethod
    def query_user_by_email(cls, email):
        return cls.objects.filter(email=email).first()
    
    def get_by_natural_key(self, email):
        return self.get(email=email)
    
    def set_transaction_pin(self, raw_pin):
        """Set transaction PIN (4-6 digits)"""
        if not raw_pin or len(str(raw_pin)) < 4 or len(str(raw_pin)) > 6:
            raise ValueError("Transaction PIN must be 4-6 digits")
        if not str(raw_pin).isdigit():
            raise ValueError("Transaction PIN must contain only digits")
        
        was_set = self.transaction_pin_set  # Check if this is a change
        self.transaction_pin = make_password(str(raw_pin))
        self.transaction_pin_set = True
        self.save(update_fields=['transaction_pin', 'transaction_pin_set'])
        
        # Apply restriction if PIN was changed (not first-time set)
        if was_set:
            self.apply_24hr_restriction()

    def verify_transaction_pin(self, raw_pin):
        """Verify transaction PIN"""
        if not self.transaction_pin_set or not self.transaction_pin:
            return False
        return check_password(str(raw_pin), self.transaction_pin)

    def set_passcode(self, raw_passcode):
        """Set 6-digit passcode for quick login"""
        raw_passcode = str(raw_passcode).strip()

        # Validation
        if not raw_passcode or len(raw_passcode) != 6:
            raise ValueError("Passcode must be exactly 6 digits")
        if not raw_passcode.isdigit():
            raise ValueError("Passcode must contain only digits")

        # Check for sequential numbers (123456, 654321)
        is_sequential_asc = all(int(raw_passcode[i]) == int(raw_passcode[i-1]) + 1 for i in range(1, 6))
        is_sequential_desc = all(int(raw_passcode[i]) == int(raw_passcode[i-1]) - 1 for i in range(1, 6))
        if is_sequential_asc or is_sequential_desc:
            raise ValueError("Passcode cannot be sequential (e.g., 123456, 654321)")

        # Check for all same digits (111111, 222222, etc.)
        if len(set(raw_passcode)) == 1:
            raise ValueError("Passcode cannot be all the same digit (e.g., 111111)")

        was_set = self.passcode_set  # Check if this is a change
        self.passcode_hash = make_password(raw_passcode)
        self.passcode_set = True
        self.save(update_fields=['passcode_hash', 'passcode_set'])
        
        # Apply restriction if passcode was changed (not first-time set)
        if was_set:
            self.apply_24hr_restriction()

    def verify_passcode(self, raw_passcode):
        """Verify 6-digit passcode"""
        if not self.passcode_set or not self.passcode_hash:
            return False
        return check_password(str(raw_passcode).strip(), self.passcode_hash)

    def apply_24hr_restriction(self):
        """Apply 24-hour transaction restriction (after PIN/passcode change)"""
        from django.utils import timezone
        from datetime import timedelta

        self.limit_restricted_until = timezone.now() + timedelta(hours=24)
        self.restricted_limit = 1000000  # ₦10,000 in kobo
        self.save(update_fields=['limit_restricted_until', 'restricted_limit'])

    def is_restricted(self):
        """Check if user is currently under 24-hour restriction"""
        from django.utils import timezone

        if not self.limit_restricted_until:
            return False
        
        if timezone.now() >= self.limit_restricted_until:
            # Auto-clear expired restriction
            self.limit_restricted_until = None
            self.restricted_limit = None
            self.save(update_fields=['limit_restricted_until', 'restricted_limit'])
            return False
        
        return True
    
    def get_effective_per_transaction_limit(self):
        """Get the effective per-transaction limit (considering restrictions)"""
        if self.is_restricted():
            return self.restricted_limit or 1000000  # ₦10,000 default
        return self.per_transaction_limit
    
    def get_effective_daily_limit(self):
        """Get the effective daily limit (considering restrictions)"""
        if self.is_restricted():
            return self.restricted_limit or 1000000  # ₦10,000 default
        return self.daily_limit
    
    def get_verified_name(self):
        """Get user's verified name from BVN or NIN"""
        # Prefer BVN name if available, then NIN, then fallback to profile name
        if self.has_bvn and self.bvn_first_name and self.bvn_last_name:
            return f"{self.bvn_first_name} {self.bvn_last_name}".strip().upper()
        elif self.has_nin and self.nin_first_name and self.nin_last_name:
            return f"{self.nin_first_name} {self.nin_last_name}".strip().upper()
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip().upper()
        return None

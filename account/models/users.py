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
 

    username = models.CharField(null=True, max_length=200)
    first_name = models.CharField(null=True, max_length=200)
    last_name = models.CharField(null=True, max_length=200)
    email = models.EmailField(null=False, unique=True)
    phone = models.CharField(null=True, max_length=20)
    address = models.CharField(null=True, max_length=200,default="")
    country = models.CharField(null=True, max_length=200,default="")
    currency = models.CharField(null=True, max_length=200,default="USD")
    dob = models.CharField(null=True, max_length=200,default="")
    state = models.CharField(null=True, max_length=200,default="")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)  # Can access admin
    is_superuser = models.BooleanField(default=False)  # Superuser status
    password = models.CharField(max_length=200)
    last_login = models.DateTimeField(blank=True, null=True)
    google_id = models.CharField(null=True, max_length=200,default="")
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
    transaction_pin = models.CharField(null=True, max_length=200, help_text="Hashed transaction PIN for withdrawals")
    transaction_pin_set = models.BooleanField(default=False, help_text="Whether user has set a transaction PIN")
 

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
        self.transaction_pin = make_password(str(raw_pin))
        self.transaction_pin_set = True
        self.save(update_fields=['transaction_pin', 'transaction_pin_set'])
    
    def verify_transaction_pin(self, raw_pin):
        """Verify transaction PIN"""
        if not self.transaction_pin_set or not self.transaction_pin:
            return False
        return check_password(str(raw_pin), self.transaction_pin)
    
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

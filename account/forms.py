from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models.users import UserModel


class StaffUserCreationForm(forms.ModelForm):
    """
    Simplified form for creating staff users without requiring all customer fields.
    Only requires essential information for admin access.
    """
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text='Enter a strong password for the staff member'
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput,
        help_text='Enter the same password again for verification'
    )

    class Meta:
        model = UserModel
        fields = ['email', 'first_name', 'last_name', 'is_staff', 'is_superuser']
        help_texts = {
            'email': 'Staff member\'s email address (used for login)',
            'first_name': 'Staff member\'s first name',
            'last_name': 'Staff member\'s last name',
            'is_staff': 'Check to allow admin panel access',
            'is_superuser': 'Check to grant all permissions (admin)',
        }

    def clean_password2(self):
        """Verify that the two password entries match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists")
        return email

    def save(self, commit=True):
        """Save the user with the password and set staff defaults"""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        # Set staff defaults
        user.is_active = True
        user.is_verified = True  # Staff don't need phone/email verification
        user.email_verified = True
        user.account_tier = 'Staff'

        # Set optional fields to avoid null issues
        if not user.phone:
            user.phone = ''
        if not user.username:
            user.username = user.email.split('@')[0]

        if commit:
            user.save()
        return user


class QuickStaffCreationForm(forms.Form):
    """
    Ultra-simplified form for quick staff creation via management command or admin action.
    """
    email = forms.EmailField(
        label='Email',
        help_text='Staff email (used for login)'
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        help_text='Temporary password (user should change on first login)'
    )
    first_name = forms.CharField(
        label='First Name',
        max_length=200
    )
    last_name = forms.CharField(
        label='Last Name',
        max_length=200
    )
    role = forms.ChoiceField(
        label='Role',
        choices=[
            ('staff', 'Staff (Basic admin access)'),
            ('admin', 'Admin (Full access)'),
        ],
        initial='staff',
        help_text='Select the access level'
    )

    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if UserModel.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists")
        return email

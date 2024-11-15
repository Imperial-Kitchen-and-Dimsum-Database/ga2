from django.core.validators import RegexValidator, MinLengthValidator
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        """Create and return a regular user with phone and password."""
        if not phone:
            raise ValueError('The phone number must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """Create and return a superuser with phone and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(phone, password, **extra_fields)
    

class CustomUser(AbstractUser):
    # Remove the username field
    username = None

    # Choices for the user_type field
    APPUSER = 'appuser'
    WORKER = 'worker'
    USER_TYPE_CHOICES = [
        (APPUSER, 'AppUser'),
        (WORKER, 'Worker'),
    ]

    # Add phone number with numeric validation and minimum length of 8 digits
    phone = models.CharField(
        max_length=15,  # Allow up to 15 digits for international numbers
        unique=True,
        validators=[
            RegexValidator(r'^\d{8,15}$', 'Phone number must be numeric and contain between 8 and 15 digits.'),
            MinLengthValidator(8)  # Ensure a minimum of 8 digits
        ]
    )

    # Add the user_type field
    user_type = models.CharField(
        max_length=7, 
        choices=USER_TYPE_CHOICES, 
        default=APPUSER,
    )

    # Override the USERNAME_FIELD to phone
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []  # No extra fields required during user creation
    objects = CustomUserManager()


    def __str__(self):
        return self.phone
    
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('phone', 'user_type', 'is_staff', 'is_active', 'date_joined')  # Customize as needed
    list_filter = ('user_type', 'is_staff', 'is_active')  # Add filters for better usability
    search_fields = ('phone',)  # Make sure to allow searching by phone number
    ordering = ('-date_joined',)

    # Define fields for the user creation form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2', 'user_type', 'is_active', 'is_staff')
        }),
    )

# Register the CustomUser model with the custom admin
admin.site.register(CustomUser, CustomUserAdmin)

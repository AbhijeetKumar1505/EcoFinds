from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.core.validators import FileExtensionValidator


class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')

        if not username:
            raise ValueError('User must have an username')

        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, email, username, password):
        user = self.create_user(
            email = self.normalize_email(email),
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
        )
        user.is_admin = True
        user.is_active = True
        user.is_staff = True
        user.is_superadmin = True
        user.save(using=self._db)
        return user



class Account(AbstractBaseUser):
    first_name      = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    username        = models.CharField(max_length=50, unique=True)
    email           = models.EmailField(max_length=100, unique=True)
    phone_number    = models.CharField(max_length=50)

    # required
    date_joined     = models.DateTimeField(auto_now_add=timezone.now)
    last_login      = models.DateTimeField(auto_now_add=timezone.now)
    is_admin        = models.BooleanField(default=False)
    is_staff        = models.BooleanField(default=False)
    is_active        = models.BooleanField(default=False)
    is_superadmin        = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, add_label):
        return True


def user_profile_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'user_{instance.user.id}/{filename}'

class UserProfile(models.Model):
    PAYMENT_METHODS = (
        ('bank', 'Bank Transfer'),
    )

    COMMUNICATION_CHOICES = (
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('call', 'Call'),
    )

    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('hi', 'Hindi'),
        ('bn', 'Bengali'),
        ('te', 'Telugu'),
        ('mr', 'Marathi'),
        ('ta', 'Tamil'),
        ('gu', 'Gujarati'),
        ('kn', 'Kannada'),
        ('ml', 'Malayalam'),
        ('pa', 'Punjabi'),
        ('ur', 'Urdu'),
        ('as', 'Assamese'),
        ('or', 'Odia'),
        ('sa', 'Sanskrit'),
        ('sd', 'Sindhi'),
        ('ne', 'Nepali'),
        ('si', 'Sinhala'),
        ('dv', 'Dhivehi'),
        ('my', 'Burmese'),
        ('th', 'Thai'),
        ('lo', 'Lao'),
        ('km', 'Khmer'),
        ('vi', 'Vietnamese'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(Account, on_delete=models.CASCADE, default=None)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    profile_picture = models.ImageField(
        upload_to=user_profile_path,
        default='default/default-user.png',
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])],
        blank=True
    )
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    country = models.CharField(blank=True, max_length=20)
    
    communication_preference = models.CharField(max_length=10, choices=COMMUNICATION_CHOICES, default='email')
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='en')
    other_language = models.CharField(max_length=50, blank=True)
    
    # Payment Details
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='bank')
    account_holder_name = models.CharField(max_length=100, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    branch_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=timezone.now)
    modified_at = models.DateTimeField(auto_now=timezone.now)
    average_seller_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_seller_reviews = models.IntegerField(default=0)

    def __str__(self):
        return self.user.email

    def full_address(self):
        return f'{self.address_line_1} {self.address_line_2}'

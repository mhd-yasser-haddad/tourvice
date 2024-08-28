from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have an username")

        user  = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user  = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


def upload_location(instance, filename):
    file_path = 'account/avatar/{account_id}/{username}-{filename}'.format(
        account_id = str(instance.id), username=str(instance.username), filename=filename
    )
    return file_path


def file_upload_location(instance, filename):
    file_path = 'account/files/{account_id}/{username}-{filename}'.format(
        account_id = str(instance.id), username=str(instance.username), filename=filename
    )
    return file_path


class Account(AbstractBaseUser):
    email               = models.EmailField(verbose_name="email", max_length=100, unique=True)
    name                = models.CharField(max_length=50, unique=True)
    username            = models.CharField(max_length=30, unique=False)
    date_joined	        = models.DateTimeField(verbose_name='date joined', auto_now_add=True)
    last_login	        = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin            = models.BooleanField(default=False)
    is_active           = models.BooleanField(default=True)
    is_staff            = models.BooleanField(default=False)
    is_superuser        = models.BooleanField(default=False)
    is_reviewer         = models.BooleanField(default=False)
    image               = models.ImageField(upload_to=upload_location, null=True)
    document            = models.FileField(upload_to=file_upload_location, null=True)
    verification_code   = models.CharField(max_length=6, null=False, default='123456')
    verified_at	        = models.DateTimeField(verbose_name='verified at', null=True)
    # birthdate           = models.DateField()
    # gender              = models.CharField(max_length=10)
    # country             = models.CharField(max_length=50)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name',]

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import redirect

class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUserModel(AbstractUser):
    username = models.CharField(unique=False, max_length=254, default="")
    email = models.EmailField(unique=True, max_length=254)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if self.username != f"{self.first_name} {self.last_name}":
            self.username = f"{self.first_name} {self.last_name}"
        return super().save(*args, **kwargs)
    




class OTPVerifyModel(models.Model):
    verify_purposes = [
        ("staff_login", "Login Staff"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="otp_instances")
    purpose = models.CharField(max_length=50, choices=verify_purposes)
    hash_otp = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    expires_at = models.DateTimeField(auto_now=False, auto_now_add=False)
    attempts = models.PositiveIntegerField(default=0) # max attemts is 5
    is_valid = models.BooleanField(default=True) # false if attempts > 5 or expired.
    verified = models.BooleanField(default=False) # true  if verified successfully
    
    def is_expired(self):
        status = timezone.now() > self.expires_at
        return status
    
    def add_attempt(self):
        self.attempts = self.attempts + 1
        return super().save(update_fields=("attempts",))

    def invalidate_otp(self):
        self.is_valid = False
        return super().save(update_fields=("is_valid",))
    
    def mark_verified(self):
        self.verified = True
        self.is_valid = False
        return super().save(update_fields=("verified", "is_valid"),)

    def save(self, *args, **kwargs):
        if self.attempts == 0:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        return super().save(*args, **kwargs)

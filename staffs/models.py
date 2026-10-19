from django.db import models
from django.contrib.auth.models import (AbstractUser, BaseUserManager,)
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.contrib.sessions.models import Session
from staffs.roles import (PERMISSIONS, ROLES,)



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
    email = models.EmailField(unique=True, max_length=254)
    first_name = None
    last_name = None
    username = None
    is_staff_member = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    profile = models.OneToOneField("staffs.UserProfileModel", null=True, verbose_name="Profile", on_delete=models.CASCADE, related_name="user")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.id or not self.profile:
            self.profile = UserProfileModel.objects.create()
        
        if not self.id:
            self.set_password(self.password)
        return super().save(*args, **kwargs)

    def change_password(self, new_password, *args, **kwargs):
        self.set_password(new_password)

        return super().save(*args, **kwargs)
        
    


class UserSession(models.Model):
    user = models.ForeignKey("staffs.CustomUserModel", on_delete=models.CASCADE)
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.profile.get_username()} - {self.session.session_key}"


    

class UserProfileModel(models.Model):
    gender_choices = [
        ("m", "Male"),
        ("f", "Female")
    ]
    
    first_name = models.CharField(unique=False, max_length=154, default="")
    last_name = models.CharField(unique=False, max_length=154, default="")
    avatar = models.ImageField(upload_to="profile/avatars/%y/%m/%d/", default="")
    role = models.CharField(max_length=75, choices=ROLES, default="")
    gender = models.CharField(max_length=10, choices=gender_choices, default="")
    nationality =  models.CharField(max_length=64, default="")
    phone = models.CharField(max_length=20, default="")
    last_updated = models.DateTimeField(auto_now=True, null=True)


    def get_default_avatar(self):
        return "https://img.icons8.com/?size=100&id=tZuAOUGm9AuS&format=png&color=000000"
    
    def get_username(self):
        return f"{self.first_name} {self.last_name}"




class OTPVerifyModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="otp_instances", null=True)
    purpose = models.CharField(max_length=80)
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


class ChangeEmailTrackModel(models.Model):
    initiated_by = models.ForeignKey("staffs.CustomUserModel", on_delete=models.CASCADE, related_name="initiated_change_emails")
    staff = models.ForeignKey("staffs.CustomUserModel", on_delete=models.CASCADE, related_name="change_email_track")
    is_valid = models.BooleanField(default=True)
    is_changed = models.BooleanField(default=False)
    is_reverted = models.BooleanField(default=False)
    new_email = models.EmailField()
    current_email = models.EmailField()
    created_at = models.DateTimeField(auto_now=False, auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)



    @property
    def is_expired(self):
        elapsed_duration = timezone.now() - self.created_at

        return (elapsed_duration.total_seconds()/60) > (60 * 24);


    @property
    def status(self):
        status = not (self.is_pending and self.is_reverted)

        return status


    def mark_changed(self):
        self.is_changed = True
        self.is_valid = False

        return super().save(update_fields=("is_changed", "is_valid", "last_updated",))


    def mark_reverted(self):
        self.is_reverted = True
        self.is_valid = False

        return super().save(update_fields=("is_reverted", "is_valid", "last_updated",))


    def invalidate(self):
        self.is_valid = False

        return super().save(update_fields=("is_valid", "last_updated",))




class RevertEmailChangeModel(models.Model):
    staff = models.OneToOneField("staffs.CustomUserModel", on_delete=models.CASCADE, related_name="revert_email_change")
    last_updated = models.DateTimeField(auto_now=True)





class StaffPermissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = PERMISSIONS["admin"]
from django.db import models
from django.contrib.auth.models import (AbstractUser, BaseUserManager,)
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

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
    
        
    

class UserProfileModel(models.Model):
    role_choices = [
        ("super_admin", "Super Administrator"),
        ("admin", "Administrator")
    ]
    gender_choices = [
        ("m", "Male"),
        ("f", "Female")
    ]
    
    first_name = models.CharField(unique=False, max_length=154, default="")
    last_name = models.CharField(unique=False, max_length=154, default="")
    avatar = models.ImageField(upload_to="profile/avatars/%y/%m/%d/", default="")
    role = models.CharField(max_length=75, choices=role_choices, default="")
    gender = models.CharField(max_length=10, choices=gender_choices, default="")
    nationality =  models.CharField(max_length=64, default="")
    phone = models.CharField(max_length=20, default="")
    last_updated = models.DateTimeField(auto_now=True, null=True)


    def get_default_avatar(self):
        return "https://img.icons8.com/?size=100&id=tZuAOUGm9AuS&format=png&color=000000"
    
    def get_username(self):
        return f"{self.first_name} {self.last_name}"




class OTPVerifyModel(models.Model):
    verify_purposes = [
        ("staff_login", "Login Staff"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name="otp_instances", null=True)
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



super_admin_permissions = [
    ("manage_roles", "Can manage roles"),
    ("manage_permissions", "Can manage permissions"),
    ("manage_super_admins", "Can manage super administrators"),
    ("view_users", "Can view users"),
    ("add_users", "Can add users"),
    ("change_users", "Can change users"),
    ("deactivate_users", "Can deactivate users"),
    ("reset_user_password", "Can reset user passwords"),
    ("view_audit_logs", "Can view audit logs"),
    ("manage_security_settings", "Can manage security settings"),
    ("manage_system_settings", "Can manage system settings"),
    ("manage_backups", "Can manage backups"),
    ("restore_backups", "Can restore backups"),
    ("view_system_logs", "Can view system logs"),
]


admin_permissions = [
    # Dashboard
    ("view_dashboard", "Can view dashboard"),
    ("view_analytics", "Can view analytics"),

    # Site
    ("manage_site", "Can manage site"),
    ("manage_homepage", "Can manage homepage"),
    ("manage_navigation", "Can manage navigation"),
    ("manage_site_settings", "Can manage site settings"),
    ("manage_seo", "Can manage SEO settings"),

    # Contents
    ("manage_contents", "Can manage contents"),
    ("manage_hero", "Can manage hero info"),

    # Team
    ("manage_team", "Can manage team"),
    ("update_team_member", "Can update team member info"),
    ("remove_team_member", "Can remove team member"),
    ("add_team_member", "Can addremove team member"),

    # Pages
    ("view_pages", "Can view pages"),
    ("add_pages", "Can add pages"),
    ("change_pages", "Can change pages"),
    ("delete_pages", "Can delete pages"),
    ("publish_pages", "Can publish pages"),

    #FAQs
    ("manage_faqs", "Can manage FAQs"),
    ("add_faq", "Can add FAQs"),
    ("update_faq", "Can update FAQs"),
    ("delete_faq", "Can delete FAQs"),

    # Services
    ("manage_services", "Can manage services"),
    ("add_service", "Can add services"),
    ("update_service", "Can update services"),
    ("delete_service", "Can delete services"),

    # Projects
    ("view_projects", "Can view projects"),
    ("add_projects", "Can add projects"),
    ("change_projects", "Can change projects"),
    ("delete_projects", "Can delete projects"),
    ("publish_projects", "Can publish projects"),

    # Blog
    ("view_blog", "Can view blog"),
    ("add_blog", "Can add blog posts"),
    ("change_blog", "Can change blog posts"),
    ("delete_blog", "Can delete blog posts"),
    ("publish_blog", "Can publish blog posts"),

    # Testimonials
    ("manage_testimonials", "Can manage testimonials"),
    ("add_testimonial", "Can add testimonials"),
    ("update_testimonial", "Can update testimonials"),
    ("delete_testimonial", "Can delete testimonials"),


    # Media Library
    ("view_media", "Can view media library"),
    ("upload_media", "Can upload media"),
    ("change_media", "Can edit media"),
    ("delete_media", "Can delete media"),

    # Messages
    ("view_messages", "Can view contact messages"),
    ("reply_messages", "Can reply to contact messages"),
    ("delete_messages", "Can delete contact messages"),

    # Quote Requests
    ("view_quotes", "Can view quote requests"),
    ("reply_quotes", "Can reply to quote requests"),
    ("delete_quotes", "Can delete quote requests"),

    # Newsletter
    ("view_subscribers", "Can view newsletter subscribers"),
    ("export_subscribers", "Can export newsletter subscribers"),
]


perms = super_admin_permissions + admin_permissions


class StaffPermissions(models.Model):
    class Meta:
        managed = False
        default_permissions = ()

        permissions = perms
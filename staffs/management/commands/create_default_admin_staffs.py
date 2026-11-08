import os
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from staffs.models import CustomUserModel
from dashboard.utils import add_new_staff




class Command(BaseCommand):
    help = "This command sets permissions to groups"


    def handle(self, *args, **options):
        try:
            default_admins = os.getenv("DEFAULT_ADMINS").split(",")

            for email in default_admins:
                email = email.strip()

                self.stdout.write(f"Adding {email} as admin staff...")

                exists = CustomUserModel.objects.filter(email=email).exists()
                is_admin = CustomUserModel.objects.filter(email=email, is_admin=True).exists()

                if is_admin or exists:
                    self.stdout.write(self.style.SUCCESS(f"{email} has been an admin. \nStaff exists: {exists}, Is admin: {is_admin}"))
                else:
                    add_new_staff(email=email, name="", action_source="management")

                    self.stdout.write(self.style.SUCCESS(f"Admin acount creation initiated. \nAn account creation completion mail has been sent to {email}. Continue the admin account creation from there."))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))
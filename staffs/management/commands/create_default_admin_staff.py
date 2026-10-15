import os
from django.utils.crypto import get_random_string
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from staffs.models import CustomUserModel




class Command(BaseCommand):
    help = "This command sets permissions to groups"


    def handle(self, *args, **options):
        try:
            existing_admin_staff = len(CustomUserModel.objects.filter(is_admin=True))
            
            if existing_admin_staff:
                self.stdout.write(self.style.SUCCESS('Default admin staff not created. Admin staffs are already existing.'))    
            else:
                server_email = os.getenv("SERVER_EMAIL")
                default_password = get_random_string(length=12)
 
                default_admin_staff = CustomUserModel.objects.create(email=server_email, password=default_password, is_staff_member=True, is_admin=True)
                default_admin_staff.profile.role = "admin"
                default_admin_staff.profile.save(update_fields=("role",))
                self.stdout.write(self.style.SUCCESS(f'Default admin staff created successfully. \nThe default login is email: "{server_email}" password: "{default_password}". \nLogin as staff, change the password and update profile info accordingly.'))

                admin_group = Group.objects.get(name="admin_group")
                admin_group.user_set.add(default_admin_staff)
            
        except:
            self.stderr(self.style.ERROR_OUTPUT("Operation not completed."))
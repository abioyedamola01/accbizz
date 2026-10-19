from django.core.management.base import BaseCommand
from django.contrib.auth.models import (Permission, Group)
from staffs.roles import (ROLES, PERMISSIONS,)



class Command(BaseCommand):
    help = "This command sets permissions to groups"


    def handle(self, *args, **options):
        try:
            group_permissions = list()

            for role, _ in ROLES:
                group = Group.objects.filter(name=f"{role}_group").first()
                permissions = [perm[0] for perm in PERMISSIONS[role]]

                group_permissions.append((group, permissions,))

            for group, permissions in group_permissions:
                permmisions_queue = Permission.objects.filter(content_type__app_label="staffs", codename__in=permissions)

                group.permissions.set(permmisions_queue)
                self.stdout.write(self.style.SUCCESS(f"{len(permmisions_queue)} has been set to {group.name}."))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))

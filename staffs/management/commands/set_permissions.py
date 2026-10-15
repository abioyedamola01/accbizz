from django.core.management.base import BaseCommand
from django.contrib.auth.models import (Permission, Group)
from staffs.models import (admin_permissions, staff_permissions)


def get_perms(perms_list):
    perms = list()
    for permission, _ in perms_list:
        perms.append(permission)
    return perms





class Command(BaseCommand):
    help = "This command sets permissions to groups"


    def handle(self, *args, **options):
        try:
            admin_group = Group.objects.filter(name="admin_group").first()
            staff_group = Group.objects.filter(name="staff_group").first()

            admin_perms_tuple_list = admin_permissions + staff_permissions
            staff_perms_tuple_list = staff_permissions

            admin_perms = get_perms(admin_perms_tuple_list)
            staff_perms = get_perms(staff_perms_tuple_list)


            group_permissions_to_add = [
                (admin_group, admin_perms),
                (staff_group, staff_perms),
            ]


            for staff_group, permissions in group_permissions_to_add:
                if staff_group:
                    permissions_to_add = Permission.objects.filter(content_type__app_label="staffs", codename__in=permissions)
                    staff_group.permissions.set(permissions_to_add)
                    self.stdout.write(self.style.SUCCESS(f"{permissions} have been set to {staff_group} group."))
                else:
                    self.stdout.write(self.style.ERROR('Set permissions not completed. Group is not found.'))
        except:
            self.stderr(self.style.ERROR_OUTPUT("Operation not completed."))
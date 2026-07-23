from django.core.management.base import BaseCommand
from django.contrib.auth.models import (Permission, Group)
from staffs.models import (super_admin_permissions, admin_permissions)


def get_perms(perms_list):
    perms = list()
    for permission, _ in perms_list:
        perms.append(permission)
    return perms





class Command(BaseCommand):
    help = "This command sets permissions to groups"


    def handle(self, *args, **options):
        try:
            super_admin_group = Group.objects.filter(name="super_admin_group").first()
            admin_group = Group.objects.filter(name="admin_group").first()

            super_admin_perms_tuple_list = super_admin_permissions + admin_permissions
            admin_perms_tuple_list = admin_permissions

            super_admin_perms = get_perms(super_admin_perms_tuple_list)
            admin_perms = get_perms(admin_perms_tuple_list)


            group_permissions_to_add = [
                (super_admin_group, super_admin_perms),
                (admin_group, admin_perms),
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
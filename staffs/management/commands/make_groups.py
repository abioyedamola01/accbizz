from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group





class Command(BaseCommand):
    help = 'A brief description of what this task does'



    def handle(self, *args, **options):
        super_admin_group, is_created_s = Group.objects.get_or_create(name="super_admin_group")
        admin_group, is_created =  Group.objects.get_or_create(name="admin_group")
        
    
        if is_created_s and is_created:
            self.stdout.write(self.style.SUCCESS('Successfully created super admin group and admin group.'))
        elif is_created_s and not is_created:
            self.stdout.write(self.style.SUCCESS('Successfully created super admin group. Admin group has been existing.'))
        elif not is_created_s and is_created:
            self.stdout.write(self.style.SUCCESS('Successfully created admin group. Super admin group has been existing.'))
        else:
            self.stdout.write(self.style.SUCCESS('Super admin group and  admin group have been existing.'))
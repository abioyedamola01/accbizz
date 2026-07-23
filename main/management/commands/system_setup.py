from django.core.management.base import BaseCommand
from dashboard.management.commands import (create_sections, create_site_instance, create_home_section_instances)
from staffs.management.commands import (create_role_groups, set_permissions)

class Command(BaseCommand):
    help = "This command calls all the commands needed for the initial setup."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("\nCreating staffs roles and groups"))
        create_role_groups.Command.handle(self)

        self.stdout.write(self.style.NOTICE("\n\nSetting permissions to groups"))
        set_permissions.Command.handle(self)


        self.stdout.write(self.style.NOTICE("\n\nCreating sections"))
        create_sections.Command.handle(self)

        self.stdout.write(self.style.NOTICE("\n\nCreating site instances"))
        create_site_instance.Command.handle(self)

        self.stdout.write(self.style.NOTICE("\n\nCreating home section instances"))
        create_home_section_instances.Command.handle(self)
        
    
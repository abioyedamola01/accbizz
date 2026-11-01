import subprocess
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from dashboard.management.commands import (create_sections, create_site_instance, create_home_section_instances)
from staffs.management.commands import (create_role_groups, set_permissions, create_default_admin_staff)

class Command(BaseCommand):
    help = "This command calls all the commands needed for the initial setup."

    def handle(self, *args, **options):
        try:
            self.stdout.write("\nMaking migrations...")
            call_command("makemigrations", interactive=False)
            self.stdout.write(self.style.SUCCESS(f"makemigrations completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))
        

        try:
            self.stdout.write("\nMigrating...")
            call_command("migrate", interactive=False)
            self.stdout.write(self.style.SUCCESS(f"migrating completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))


        # npm run build
        try:
            self.stdout.write('\nRunning "npm run build"...')
            result = subprocess.run(
                ['npm', 'run', 'build'],
                capture_output=True,
                text=True,
                check=True,
                cwd=settings.BASE_DIR 
            )
            self.stdout.write(result.stdout)
            self.stdout.write(self.style.SUCCESS('Tailwind CSS successfully built and minified.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))


        # collectstatic
        try:
            self.stdout.write("\nCollecting static files...")
            call_command("collectstatic", interactive=False)
            self.stdout.write(self.style.SUCCESS(f"Files collected"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))
        

        
        self.stdout.write("\nCreating staffs roles and groups...")
        create_role_groups.Command.handle(self)

        self.stdout.write("\nSetting permissions to groups...")
        set_permissions.Command.handle(self)


        self.stdout.write("\nCreating default admin user...")
        create_default_admin_staff.Command.handle(self)

        self.stdout.write("\nCreating sections...")
        create_sections.Command.handle(self)

        self.stdout.write("\nCreating site instances...")
        create_site_instance.Command.handle(self)

        self.stdout.write("\nCreating home section instances...")
        create_home_section_instances.Command.handle(self)
        
    
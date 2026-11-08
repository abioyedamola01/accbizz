from django.core.management import call_command
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "One-time initial data setup (safe to re-run)."

    def handle(self, *args, **options):
        steps = [
            "create_role_groups",
            "set_permissions",
            "create_default_admin_staffs",
            "create_sections",
            "create_site_instance",
            "create_home_section_instances",
        ]
        for name in steps:
            self.stdout.write(f"Running {name}...")
            call_command(name)  # an error here stops the command
        self.stdout.write(self.style.SUCCESS("Initial setup complete."))
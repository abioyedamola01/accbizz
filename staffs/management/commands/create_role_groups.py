from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group





class Command(BaseCommand):
    help = 'This command creates roles groups and commit them to the db.'


    def handle(self, *args, **options):
        try:
            roles = ("admin", "staff",)

            for role in roles:
                _, is_created = Group.objects.get_or_create(name=f"{role}_group")
                
                if is_created:
                    self.stdout.write(self.style.SUCCESS(f"Successfully created {role} group."))
                elif not is_created:
                    self.stdout.write(self.style.SUCCESS(f"{role} group has been existing."))
        except:
            self.stderr(self.style.ERROR_OUTPUT("Operation not completed."))
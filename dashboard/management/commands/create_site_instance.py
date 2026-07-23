from django.core.management.base import BaseCommand
from dashboard.models import SiteModel


class Command(BaseCommand):
    help = 'This command creates site instance and prepopulate fields ith dummy values.'

    def handle(self, *args, **options):
        try:
            if SiteModel.objects.first():
                self.stdout.write(self.style.SUCCESS('Site instance is already existing.'))
            else:
                SiteModel.objects.create(company_name="Company name", display_name="Display", domain_url="url.com")
                self.stdout.write(self.style.SUCCESS("Site instances created successfully. Fields are prepopuated with dummy values, ensure adding appropriate values."))
        except:
            self.stderr.write(self.style.ERROR_OUTPUT("Operation not completed"))
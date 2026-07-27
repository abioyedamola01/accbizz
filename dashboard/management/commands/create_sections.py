from django.core.management.base import BaseCommand
from dashboard.models import (HeroSectionModel, AboutSectionModel,)


class Command(BaseCommand):
    help = 'This command creates all sections instance.'

    def handle(self, *args, **options):
        # Hero section model instance creation
        try:
            _, hero_is_created = HeroSectionModel.objects.get_or_create(name="hero")

            if hero_is_created:
                self.stdout.write(self.style.SUCCESS("Hero section has been created successfully and its fields have been prepopulated with dummy values. Ensure you add original values."))
            else:
                self.stdout.write(self.style.SUCCESS("Hero section has been existing."))
        except:
            self.stderr.write(self.style.ERROR_OUTPUT("Operation not completed. Could not create hero section."))


        # About section model instance creation
        try:
            _, about_is_created = AboutSectionModel.objects.get_or_create(name="about")

            if about_is_created:
                self.stdout.write(self.style.SUCCESS("About section has been created successfully and its fields have been prepopulated withdummy values. Ensure you add original values."))
            else:
                self.stdout.write(self.style.SUCCESS("About section has been existing."))
        except:
            pass
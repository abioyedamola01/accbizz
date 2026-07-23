from django.core.management.base import BaseCommand
from dashboard.models import HeroSectionModel


class Command(BaseCommand):
    help = 'This command creates all sections instance.'

    def handle(self, *args, **options):
        # Hero section creation
        try:
            hero_section, is_created = HeroSectionModel.objects.get_or_create(name="hero")

            if is_created:
                hero_section.title = "Dummy Hero Section Title"
                hero_section.sub_title = "Dummy Hero subtitle text. Ensure you change it to  original contents."
                hero_section.save()
                self.stdout.write(self.style.SUCCESS("Hero section has been created successfully and its fields have been prepopulated with dummy values. Ensure you add original values."))
            else:
                self.stdout.write(self.style.SUCCESS("Hero section has been existing."))
        except:
            self.stderr.write(self.style.ERROR_OUTPUT("Operation not completed. Could not save hero section."))
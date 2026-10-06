from django.core.management.base import BaseCommand
from dashboard.models import HomeSectionModel


class Command(BaseCommand):
    help = "This command creates home sections instances."

    def handle(self, *args, **options):
        try:
            home_sections = [
                ("hero", 0, "Homepage headline, description, call-to-action buttons, and hero media."),
                ("about", 1, "Introduction with a brief overview, supporting image"),
                ("services", 2, "Services with a brief introduction, featured service cards."),
            ]

            for section, order, blurb in home_sections:
                section_instance, is_created = HomeSectionModel.objects.get_or_create(name=section)
                if is_created:
                    section_instance.order = order
                    section_instance.blurb = blurb
                    section_instance.save()
                    self.stdout.write(self.style.SUCCESS(f"{section} home section has been created successfully."))
                else:
                    self.stdout.write(self.style.SUCCESS(f"{section} home section has been existing."))
        except:
            self.stderr.write(self.style.ERROR_OUTPUT("Operation not completed"))
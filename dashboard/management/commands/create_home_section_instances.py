from django.core.management.base import BaseCommand
from dashboard.models import (HomeSectionModel, SiteModel,)


class Command(BaseCommand):
    help = "This command creates home sections instances."

    def handle(self, *args, **options):
        try:
            home_sections = [
                ("hero", 0, "Homepage headline, description, call-to-action buttons, and hero media."),
                ("about", 1, "Introduction with a brief overview, supporting image"),
                ("services", 2, "Services with a brief introduction, featured service cards."),
                ("testimonials", 3, "Compelling introduction with seamlessly integrate social proof.")
            ]

            

            for name, order, blurb in home_sections:
                section_instance = HomeSectionModel.objects.filter(name=name).first()

                if not section_instance:
                    site_inst = SiteModel.objects.first()
                    HomeSectionModel.objects.create(name=name, blurb=blurb, order=order, site=site_inst)
                    self.stdout.write(self.style.SUCCESS(f"{name} home section has been created successfully."))
                else:
                    self.stdout.write(self.style.SUCCESS(f"{name} home section has been existing."))
             
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))
        
            
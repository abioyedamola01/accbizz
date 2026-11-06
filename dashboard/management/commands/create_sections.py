from django.core.management.base import BaseCommand
from dashboard.models import (HeroSectionModel, AboutSectionModel,)


class Command(BaseCommand):
    help = 'This command creates all sections instance.'

    def handle(self, *args, **options):
        # Hero section model instance creation
        try:
            hero, hero_is_created = HeroSectionModel.objects.get_or_create(name="hero")
            img_url = "https://images.unsplash.com/photo-1523240795612-9a054b0db644?q=80&w=1400&auto=format&fit=crop"
            img_saved = hero.save_img(url=img_url)

            
            if hero_is_created:
                self.stdout.write(self.style.SUCCESS("Hero section has been created successfully and its fields have been prepopulated with dummy values. Ensure you add original values."))    

                if img_saved: self.stdout.write(self.style.SUCCESS("Hero image saved successfully."))
                
            else:
                self.stdout.write(self.style.SUCCESS("Hero section has been existing."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))
        

        # About section model instance creation
        try:
            about, about_is_created = AboutSectionModel.objects.get_or_create(name="about")

            img1_url = "https://plus.unsplash.com/premium_photo-1664372145543-d60ba2756a7e?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1yZWxhdGVkfDJ8fHxlbnwwfHx8fHw%3D"
            img2_url = "https://images.unsplash.com/photo-1619296330981-b882d7e93425?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8dW5pdmVyc2l0eSUyMHN0dWRlbnQlMjBzdHVkeWluZ3xlbnwwfHwwfHx8MA%3D%3D"
            
            img1_saved = about.save_img(url=img1_url, img="img1")
            img2_saved = about.save_img(url=img2_url, img="img2")
                        
            if about_is_created:
                self.stdout.write(self.style.SUCCESS("About section has been created successfully and its fields have been prepopulated withdummy values. Ensure you add original values."))

                if img1_saved: self.stdout.write(self.style.SUCCESS("About img1 saved successfully."))
                if img2_saved: self.stdout.write(self.style.SUCCESS("About img2 saved successfully."))
                                

            else:
                self.stdout.write(self.style.SUCCESS("About section has been existing."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Operation not completed. Error: {e}"))
        
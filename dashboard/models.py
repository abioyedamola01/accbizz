from django.db import models
from django.utils.text import slugify

# Create your models here.



class HeroSectionModel(models.Model):
    name = models.CharField(max_length=50, default="hero")
    title = models.CharField(max_length=60, default="Dummy Hero Section Title")
    sub_title = models.CharField(max_length=200, default="Dummy Hero subtitle text. Ensure you change it to  original contents.")
    img =  models.ImageField(upload_to="hero/%y/%m/%d/", default="")







class AboutSectionModel(models.Model):
    name = models.CharField(max_length=50, default="about")
    description = models.TextField(default="About section has been created successfully and its fields have been prepopulated withdummy values. Ensure you add original values.")
    story =  models.TextField(default="About section has been created successfully and its fields have been prepopulated withdummy values. Ensure you add original values.")
    mission = models.TextField(default="About section has been created successfully and its fields have been prepopulated withdummy values. Ensure you add original values.")
    vision = models.TextField(default="About section has been created successfully and its fields have been prepopulated withdummy values. Ensure you add original values.")



class TeamModel(models.Model):
    avatar = models.ImageField(upload_to="team/avatars/%y/%m/%d/", null=True)
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=50)
    email = models.EmailField(max_length=254)
    slug = models.SlugField(default="", null=True)
    is_member = models.BooleanField(default=True, null=True)
    about = models.ForeignKey("dashboard.AboutSectionModel", on_delete=models.SET_NULL, related_name="team", null=True)


    def save(self, *args, **kwargs):
        if not self.id:
            self.about = AboutSectionModel.objects.first()
            super().save(*args, **kwargs)
            self.slug = f"{self.id}-{slugify(self.name)}"
            return super().save(update_fields=("slug",))
        return super().save(*args, **kwargs)

    def get_default_avatar(self):
        return "https://img.icons8.com/?size=100&id=tZuAOUGm9AuS&format=png&color=000000"

    def remove_as_member(self):
        self.is_member = False
        return super().save(update_fields=("is_member",))




class SiteModel(models.Model):
    company_name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=10)
    domain_url = models.URLField(default="")
    last_updated = models.DateTimeField(auto_now=True, null=True)
    hero = models.OneToOneField("dashboard.HeroSectionModel", on_delete=models.SET_NULL, null=True)
    about = models.OneToOneField("dashboard.AboutSectionModel", on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.company_name} ({self.display_name})"
    
    def save(self, *args, **kwargs):
        if not self.id:
            self.hero = HeroSectionModel.objects.first()
            self.about = AboutSectionModel.objects.first()
        return super().save(*args, **kwargs)
    


class HomeSectionModel(models.Model):
    name = models.CharField(max_length=86)
    blurb = models.CharField(max_length=243, default="")
    slug = models.SlugField(unique=True, null=True)
    order = models.PositiveIntegerField(null=True)
    is_enabled = models.BooleanField(default=True)
    site = models.ForeignKey("dashboard.SiteModel", on_delete=models.CASCADE, related_name="sections")
    

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id or not self.site:
            site_instance = SiteModel.objects.first()
            self.site = site_instance if site_instance else None

        if self.id and not self.slug:
            self.slug = f"{self.id}-{slugify(self.name)}"

        return super().save(*args, **kwargs)

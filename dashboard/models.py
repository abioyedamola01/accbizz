from django.db import models
from django.utils.text import slugify

# Create your models here.



class HeroSectionModel(models.Model):
    name = models.CharField(max_length=50, default="hero")
    title = models.CharField(max_length=60, default="")
    sub_title = models.CharField(max_length=200, default="")
    img =  models.ImageField(upload_to="hero/%y/%m/%d", default="")



class SiteModel(models.Model):
    company_name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=10)
    domain_url = models.URLField(default="")
    last_updated = models.DateTimeField(auto_now=True, null=True)
    hero = models.OneToOneField("dashboard.HeroSectionModel", on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"{self.company_name} ({self.display_name})"
    
    def save(self, *args, **kwargs):
        if not self.id or not self.hero:
            self.hero = HeroSectionModel.objects.first()
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

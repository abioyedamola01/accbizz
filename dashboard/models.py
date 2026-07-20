from django.db import models
from django.utils.text import slugify

# Create your models here.



class SiteModel(models.Model):
    company_name = models.CharField(max_length=50)
    display_name = models.CharField(max_length=10)
    domain_url = models.URLField(default="")
    last_updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return f"{self.company_name} ({self.display_name})"
    



class HomeSectionModel(models.Model):
    block_type_choices = []

    name = models.CharField(max_length=86)
    blurb = models.CharField(max_length=243, default="")
    slug = models.SlugField(unique=True, null=True)
    order = models.PositiveIntegerField()
    is_enabled = models.BooleanField(default=True)
    site = models.ForeignKey(SiteModel, on_delete=models.CASCADE, related_name="sections")
    block_type = models.CharField(max_length=50, choices=block_type_choices)
    last_updated = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id or not self.site:
            site_instance = SiteModel.objects.first()
            self.site = site_instance if site_instance else None
        
        if not self.id or not self.slug:
            self.slug = f"{self.id}-{slugify(self.name)}"

        return super().save(*args, **kwargs)
    
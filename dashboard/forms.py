from django import forms
from staffs.models import UserProfileModel
from .models import (SiteModel, HomeSectionModel, HeroSectionModel, AboutSectionModel, TeamModel, FAQsModel)


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfileModel
        fields = ("first_name", "last_name", "gender", "nationality", "phone",)


class UpdateAvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfileModel
        fields = ("avatar",)



class SiteInfoForm(forms.ModelForm): 
    class Meta:
        model = SiteModel
        fields = ("company_name", "display_name")


class SiteHomeSectionUpdateForm(forms.ModelForm):
    class Meta:
        model = HomeSectionModel
        fields = ("order", "is_enabled",)

SiteHomeSectionUpdateFormset =  forms.modelformset_factory(HomeSectionModel, form=SiteHomeSectionUpdateForm, extra=0)
        

class HeroInfoForm(forms.ModelForm):
    class Meta:
        model = HeroSectionModel
        fields = ("title", "sub_title",)

class HeroImgForm(forms.ModelForm):
    class Meta:
        model = HeroSectionModel
        fields = ("img",)



class AboutForm(forms.ModelForm):
    class Meta:
        model = AboutSectionModel
        fields = ("description", "story", "mission", "vision",)


class TeamForm(forms.ModelForm):
    class Meta:
        model = TeamModel
        fields = ("avatar", "name", "email", "role", )


class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQsModel
        fields = ("question", "answer",)
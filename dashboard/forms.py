from django import forms
from staffs.models import UserProfileModel
from .models import (SiteModel, HomeSectionModel,)


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
        

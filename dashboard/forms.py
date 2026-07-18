from django import forms
from django.forms.models import model_to_dict
from staffs.models import (
    CustomUserModel,
    UserProfileModel
)



class EditProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfileModel
        fields = ("first_name", "last_name", "gender", "nationality", "phone",)




class UpdateAvatarForm(forms.ModelForm):
    class Meta:
        model = UserProfileModel
        fields = ("avatar",)

from django import  forms



class StaffLoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(required=True, widget=forms.PasswordInput())


class VerifyOTPForm(forms.Form):
    otp_code = forms.CharField(max_length=6, widget=forms.NumberInput)


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(required=True, widget=forms.PasswordInput())
    new_password = forms.CharField(required=True, widget=forms.PasswordInput())


class PasswordForm(forms.Form):
    password = forms.CharField(required=True, widget=forms.PasswordInput())

class ChangeEmailForm(forms.Form):
    current_email = forms.EmailField()
    new_email = forms.EmailField()
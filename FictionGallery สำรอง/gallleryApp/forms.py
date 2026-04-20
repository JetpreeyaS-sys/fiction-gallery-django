from django import forms
from gallleryApp.models import User

class RegisterForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput,
    label="Password",
    )

class Meta:
    model = User
    fields = ['username', 'password', 'role']

    widgets = {
        "role": forms.RadioSelect,
    }
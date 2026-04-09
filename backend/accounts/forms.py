from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label="Όνομα")
    last_name = forms.CharField(required=True, label="Επώνυμο")

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")
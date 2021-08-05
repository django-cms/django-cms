from django import forms
from django.contrib.auth.forms import AuthenticationForm

from cms.test_utils.project.sampleapp.models import Category


class LoginForm(AuthenticationForm):
    pass


class LoginForm2(AuthenticationForm):
    pass


class LoginForm3(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)


class SampleWizardForm(forms.ModelForm):

    class Meta:
        model = Category
        exclude = []

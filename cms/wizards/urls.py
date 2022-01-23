from django.urls import re_path

from .views import WizardCreateView

urlpatterns = [
    re_path(r"^create/$",
            WizardCreateView.as_view(), name="cms_wizard_create"),
]

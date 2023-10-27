from django.urls import path

from .views import WizardCreateView

urlpatterns = [
    path("create/", WizardCreateView.as_view(), name="cms_wizard_create"),
]

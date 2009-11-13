from django import forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

def get_copy_dialog_form(request):
    fields = {}
    if settings.CMS_PERMISSION:
        fields['copy_permissions'] = forms.BooleanField(label=_('Copy permissions'), required=False, initial=True)
    
    if settings.CMS_MODERATOR:
        fields['copy_moderation'] = forms.BooleanField(label=_('Copy moderation'), required=False, initial=True)
    Form = type('CopyDialogForm', (forms.BaseForm,), { 'base_fields': fields })
    return Form
from django import forms
from django.utils.translation import ugettext_lazy as _
from cms import settings as cms_settings

def get_copy_dialog_form(request):
    fields = {}
    if cms_settings.CMS_PERMISSION:
        fields['copy_permissions'] = forms.BooleanField(label=_('Copy permissions'), required=False, initial=True)
    
    if cms_settings.CMS_MODERATOR:
        fields['copy_moderation'] = forms.BooleanField(label=_('Copy moderation'), required=False, initial=True)
    Form = type('CopyDialogForm', (forms.BaseForm,), { 'base_fields': fields })
    return Form
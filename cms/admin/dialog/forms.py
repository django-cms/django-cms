# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _


class PermissionForm(forms.Form):
    """
    Holds the specific field for permissions
    """
    copy_permissions = forms.BooleanField(label=_('Copy permissions'),
                                          required=False, initial=True)

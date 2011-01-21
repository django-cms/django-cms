# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

class PermissionForm(forms.Form):
    '''
    Holds the specific field for permissions
    '''
    copy_permissions = forms.BooleanField(label=_('Copy permissions'), 
                                          required=False, initial=True)
    
class ModeratorForm(forms.Form):
    '''
    Holds the specific field for moderator
    '''
    copy_moderation = forms.BooleanField(label=_('Copy moderation'), 
                                         required=False, initial=True)
    
class PermissionAndModeratorForm(PermissionForm, ModeratorForm):
    '''
    Subclass of both ModeratorForm AND PermissionForm, thus it inherits both 
    fields
    '''
    pass

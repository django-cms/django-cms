# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from cms.stacks.models import Stack


class StackInsertionForm(forms.Form):
    INSERT_COPY = 'copy'
    INSERT_LINK = 'link'
    INSERTION_CHOICES = (
        (INSERT_COPY, _('copy')),
        (INSERT_LINK, _('link')),
    )
    stack = forms.ModelChoiceField(label=_('stack'), required=True, queryset=Stack.objects.all())
    insertion_type = forms.ChoiceField(label=_('insertion type'), choices=INSERTION_CHOICES, required=True, initial=INSERT_LINK)
    language_code = forms.CharField(label=_('language code'), widget=forms.HiddenInput, required=True)


class StackCreationForm(forms.ModelForm):
    class Meta:
        model = Stack
        exclude = 'content'

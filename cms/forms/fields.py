# -*- coding: utf-8 -*-
from django import forms
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.forms.fields import EMPTY_VALUES
from django.utils.translation import ugettext_lazy as _

from cms.forms.utils import get_site_choices, get_page_choices
from cms.forms.widgets import PageSelectWidget, PageSmartLinkWidget
from cms.models.pagemodel import Page


class SuperLazyIterator(object):
    def __init__(self, func):
        self.func = func

    def __iter__(self):
        return iter(self.func())


class LazyChoiceField(forms.ChoiceField):
    def _set_choices(self, value):
        # we overwrite this function so no list(value) is called
        self._choices = self.widget.choices = value

    choices = property(forms.ChoiceField._get_choices, _set_choices)


class PageSelectFormField(forms.MultiValueField):
    widget = PageSelectWidget
    default_error_messages = {
        'invalid_site': _(u'Select a valid site'),
        'invalid_page': _(u'Select a valid page'),
    }

    def __init__(self, queryset=None, empty_label=u"---------", cache_choices=False,
                 required=True, widget=None, to_field_name=None, limit_choices_to=None,
                  *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        site_choices = SuperLazyIterator(get_site_choices)
        page_choices = SuperLazyIterator(get_page_choices)
        self.limit_choices_to = limit_choices_to
        kwargs['required'] = required
        fields = (
            LazyChoiceField(choices=site_choices, required=False, error_messages={'invalid': errors['invalid_site']}),
            LazyChoiceField(choices=page_choices, required=False, error_messages={'invalid': errors['invalid_page']}),
        )
        super(PageSelectFormField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            page_id = data_list[1]

            if page_id in EMPTY_VALUES:
                if not self.required:
                    return None
                raise forms.ValidationError(self.error_messages['invalid_page'])
            return Page.objects.get(pk=page_id)
        return None

    def has_changed(self, initial, data):
        is_empty = data and (len(data) >= 2 and data[1] in [None, ''])

        if isinstance(self.widget, RelatedFieldWidgetWrapper):
            self.widget.decompress = self.widget.widget.decompress

        if is_empty and initial is None:
            # when empty data will have [u'1', u'', u''] as value
            # this will cause django to always return True because of the '1'
            # so we simply follow django's default behavior when initial is None and data is "empty"
            data = ['' for x in range(0, len(data))]
        return super(PageSelectFormField, self).has_changed(initial, data)

    def _has_changed(self, initial, data):
        return self.has_changed(initial, data)

class PageSmartLinkField(forms.CharField):
    widget = PageSmartLinkWidget

    def __init__(self, max_length=None, min_length=None, placeholder_text=None,
                 ajax_view=None, *args, **kwargs):
        self.placeholder_text = placeholder_text
        widget = self.widget(ajax_view=ajax_view)
        super(PageSmartLinkField, self).__init__(max_length, min_length,
                                                 widget=widget, *args, **kwargs)

    def widget_attrs(self, widget):
        attrs = super(PageSmartLinkField, self).widget_attrs(widget)
        attrs.update({'placeholder_text': self.placeholder_text})
        return attrs

import warnings

from django import forms
from django.contrib.admin.widgets import RelatedFieldWidgetWrapper
from django.core.validators import EMPTY_VALUES
from django.forms import ChoiceField
from django.utils.translation import gettext_lazy as _

from cms.forms.utils import get_page_choices, get_site_choices
from cms.forms.validators import validate_url
from cms.forms.widgets import PageSelectWidget, PageSmartLinkWidget
from cms.models.pagemodel import Page
from cms.utils.compat import DJANGO_4_2
from cms.utils.compat.warnings import RemovedInDjangoCMS42Warning


class SuperLazyIterator:
    def __init__(self, func):
        warnings.warn("SuperLazyIterator is deprecated.",
                      RemovedInDjangoCMS42Warning, stacklevel=2)
        self.func = func

    def __iter__(self):
        return iter(self.func())


class LazyChoiceField(forms.ChoiceField):

    def __init__(self, *args, **kwargs):
        warnings.warn("LazyChoiceField is deprecated. Use Django's ChoiceField instead.",
                      RemovedInDjangoCMS42Warning, stacklevel=2)
        super().__init__(*args, **kwargs)

    @property
    def choices(self):
        return self._choices

    @choices.setter
    def choices(self, value):
        # we overwrite this function so no list(value) or normalize_choices(value) is called
        # also, do not call the widget's setter as of Django 5
        if DJANGO_4_2:
            self._choices = self.widget.choices = value
        else:
            self._choices = self.widget._choices = value


class PageSelectFormField(forms.MultiValueField):
    """
    Behaves like a :class:`django.forms.ModelChoiceField` field for the
    :class:`cms.models.pagemodel.Page` model, but displays itself as a split
    field with a select drop-down for the site and one for the page. It also
    indents the page names based on what level they're on, so that the page
    select drop-down is easier to use. This takes the same arguments as
    :class:`django.forms.ModelChoiceField`.
    """
    widget = PageSelectWidget
    default_error_messages = {
        'invalid_site': _('Select a valid site'),
        'invalid_page': _('Select a valid page'),
    }

    def __init__(self, queryset=None, empty_label="---------", cache_choices=False,
                 required=True, widget=None, to_field_name=None, limit_choices_to=None, *args, **kwargs):
        errors = self.default_error_messages.copy()
        if 'error_messages' in kwargs:
            errors.update(kwargs['error_messages'])
        self.limit_choices_to = limit_choices_to
        kwargs['required'] = required
        fields = (
            ChoiceField(choices=get_site_choices, required=False, error_messages={'invalid': errors['invalid_site']}),
            ChoiceField(choices=get_page_choices, required=False, error_messages={'invalid': errors['invalid_page']}),
        )

        # Remove the unexpected blank kwarg if it's supplied,
        # causes an error where the MultiValueField doesn't expect it
        # https://github.com/django/django/commit/da79ee472d803963dc3ea81ee67767dc06068aac
        if 'blank' in kwargs:
            del kwargs['blank']

        super().__init__(fields, *args, **kwargs)

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
        return super().has_changed(initial, data)

    def _has_changed(self, initial, data):
        return self.has_changed(initial, data)


class PageSmartLinkField(forms.CharField):
    """
    A field making use of ``cms.forms.widgets.PageSmartLinkWidget``.
    This field will offer you a list of matching internal pages as you type.
    You can either pick one or enter an arbitrary URL to create a non-existing entry.
    Takes a `placeholder_text` argument to define the text displayed inside the
    input before you type.

    The widget uses an ajax request to try to find pages match. It will try to find
    case-insensitive matches amongst public and published pages on the `title`, `path`,
    `page_title`, `menu_title` fields.
    """
    widget = PageSmartLinkWidget
    default_validators = [validate_url]

    def __init__(self, max_length=None, min_length=None, placeholder_text=None,
                 ajax_view=None, *args, **kwargs):
        self.placeholder_text = placeholder_text
        widget = self.widget(ajax_view=ajax_view)
        super().__init__(
            max_length=max_length, min_length=min_length, widget=widget, *args, **kwargs
        )

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.update({'placeholder_text': self.placeholder_text})
        return attrs

    def clean(self, value):
        value = self.to_python(value).strip()
        return super().clean(value)

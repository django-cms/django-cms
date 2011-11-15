# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.core import exceptions
from django.db import models
from django.forms.fields import TypedChoiceField
from django.utils.text import capfirst
from django.core import validators

class NamedFlagsFormField(forms.fields.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple

class NamedFlagsField(models.Field):
    __metaclass__ = models.SubfieldBase
    def __init__(self, *args, **kwargs):
        null, blank = kwargs.pop('null',False), kwargs.pop('blank', True)
        choices = kwargs.pop('choices', settings.CMS_PAGE_FLAGS)
        super(NamedFlagsField, self).__init__(*args, null=null, blank=blank, choices=choices, **kwargs)
    def get_internal_type(self):
        return 'TextField'
    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect ourselves, since we inherit.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        kwargs['null'] = True
        kwargs['blank'] = True
        return (field_class, args, kwargs)
    def to_python(self, value):
        if isinstance(value, list):
            return value
        if value:
            return value.split(',')
        return []
    def get_db_prep_value(self, value):
        if isinstance(value, list):
            active_flags = value
        else:
            active_flags = []
        return ','.join(active_flags)
    def formfield(self, form_class=forms.CharField, **kwargs):
        "Returns a django.forms.Field instance for this database Field."
        defaults = {'required': not self.blank, 'label': capfirst(self.verbose_name), 'help_text': self.help_text}
        if self.has_default():
            if callable(self.default):
                defaults['initial'] = self.default
                defaults['show_hidden_initial'] = True
            else:
                defaults['initial'] = self.get_default()
        defaults['choices'] = self.get_choices(include_blank=False)
        form_class = NamedFlagsFormField
        for k in kwargs.keys():
            if k not in ('choices', 'required',
                         'widget', 'label', 'initial', 'help_text',
                         'error_messages', 'show_hidden_initial'):
                del kwargs[k]
        defaults.update(kwargs)
        return form_class(**defaults)
    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. Subclasses should override
        this to provide validation logic.
        """
        if not self.editable:
            # Skip validation for non-editable fields.
            return
        choices = [c[0] for c in self._choices]
        if self._choices and value:
            for val in value:
                if not val in choices:
                    raise exceptions.ValidationError(self.error_messages['invalid_choice'] % val)

        if value is None and not self.null:
            raise exceptions.ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise exceptions.ValidationError(self.error_messages['blank'])
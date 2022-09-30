from django.db import models

from cms.forms.fields import PageSelectFormField
from cms.models.placeholdermodel import Placeholder


class PlaceholderField(models.ForeignKey):

    def __init__(self, slotname, default_width=None, actions=None, **kwargs):
        from cms.utils.placeholder import PlaceholderNoAction, validate_placeholder_name

        if not actions:
            actions = PlaceholderNoAction

        if kwargs.get('related_name', None) == '+':
            raise ValueError("PlaceholderField does not support disabling of related names via '+'.")
        if not callable(slotname):
            validate_placeholder_name(slotname)
        self.slotname = slotname
        self.default_width = default_width
        self.actions = actions()
        kwargs.update({'null': True})  # always allow Null
        kwargs.update({'editable': False}) # never allow edits in admin
        # We hard-code the `to` argument for ForeignKey.__init__
        # since a PlaceholderField can only be a ForeignKey to a Placeholder
        kwargs['to'] = 'cms.Placeholder'
        kwargs['on_delete'] = kwargs.get('on_delete', models.CASCADE)
        super().__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['slotname'] = self.slotname
        return name, path, args, kwargs

    def _get_new_placeholder(self, instance):
        return Placeholder.objects.create(slot=self._get_placeholder_slot(instance), default_width=self.default_width)

    def _get_placeholder_slot(self, model_instance):
        from cms.utils.placeholder import validate_placeholder_name

        if callable(self.slotname):
            slotname = self.slotname(model_instance)
            validate_placeholder_name(slotname)
        else:
            slotname = self.slotname
        return slotname

    def pre_save(self, model_instance, add):
        if not model_instance.pk:
            setattr(model_instance, self.name, self._get_new_placeholder(model_instance))
        else:
            slot = self._get_placeholder_slot(model_instance)
            placeholder = getattr(model_instance, self.name)
            if not placeholder:
                setattr(model_instance, self.name, self._get_new_placeholder(model_instance))
                placeholder = getattr(model_instance, self.name)
            if placeholder.slot != slot:
                placeholder.slot = slot
                placeholder.save()
        return super().pre_save(model_instance, add)

    def save_form_data(self, instance, data):
        data = getattr(instance, self.name, '')
        if not isinstance(data, Placeholder):
            data = self._get_new_placeholder(instance)
        super().save_form_data(instance, data)

    def contribute_to_class(self, cls, name):
        super().contribute_to_class(cls, name)
        if not hasattr(cls._meta, 'placeholder_field_names'):
            cls._meta.placeholder_field_names = []
        if not hasattr(cls._meta, 'placeholder_fields'):
            cls._meta.placeholder_fields = {}
        cls._meta.placeholder_field_names.append(name)
        cls._meta.placeholder_fields[self] = name
        self.model = cls


class PageField(models.ForeignKey):
    default_form_class = PageSelectFormField

    def __init__(self, **kwargs):
        # We hard-code the `to` argument for ForeignKey.__init__
        # since a PageField can only be a ForeignKey to a Page
        kwargs['to'] = 'cms.Page'
        kwargs['on_delete'] = kwargs.get('on_delete', models.CASCADE)
        super().__init__(**kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': self.default_form_class,
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

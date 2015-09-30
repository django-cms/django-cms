# -*- coding: utf-8 -*-

from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.utils.translation import override as force_language, force_text


class WizardBase(object):
    supports_safe_delete = True
    template_name = None

    def __init__(self, title, weight, form,
                 model=None, admin_model=None,
                 template_name=None,
                 inlineformset=None, inlineformset_title=''):
        self.title = title
        self.weight = weight
        self.form = form
        self.model = model
        self.admin_model = admin_model
        if template_name is not None:
            self.template_name = template_name
        self.inlineformset = inlineformset
        self.inlineformset_title = inlineformset_title


@python_2_unicode_compatible
class Wizard(WizardBase):
    template_name = 'cms/wizards/create.html'

    @property
    def id(self):
        content_type = ContentType.objects.get_for_model(self.get_model())
        return content_type.pk

    def __str__(self):
        return self.title

    def __repr__(self):
        return 'Wizard: "{0}"'.format(force_text(self.title))

    def user_has_add_permission(self, user):
        """
        Returns whether the given «user» has permission to add instances of this
        wizard's associated model. Can be overridden as required for more
        complex situations.
        :param user: The current user using the wizard.
        :return: True if the user should be able to use this wizard.
        """
        app_label = self.model._meta.app_label
        model_name = self.model.__name__.lower()
        return user.has_perm("%s.%s_%s" % (app_label, "add", model_name))

    def get_success_url(self, obj, *args, **kwargs):
        """This should return the URL of the created object."""
        if 'language' in kwargs:
            with force_language(kwargs['language']):
                return obj.get_absolute_url()
        else:
            return obj.get_absolute_url()

    def get_model(self):
        if self.model:
            return self.model
        if issubclass(self.form, ModelForm):
            return self.form._meta.model
        raise ImproperlyConfigured(u"Please set entry 'model' attribute or use "
                                   u"ModelForm subclass as a form")

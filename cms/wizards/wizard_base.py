# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.encoding import python_2_unicode_compatible
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.utils.translation import override as force_language


class WizardBase(object):
    supports_safe_delete = True
    template_name = None

    def __init__(self, title, weight, form, edit_form=None,
                 cms_app_title=None, cms_app_slug=None, cms_app=None,
                 model=None, admin_model=None,
                 template_name=None,
                 inlineformset=None, inlineformset_title=''):
        self.title = title
        self.weight = weight
        self.form = form
        self.edit_form = edit_form if edit_form else form
        self.model = model
        self.admin_model = admin_model
        if template_name is not None:
            self.template_name = template_name
        self.inlineformset = inlineformset
        self.inlineformset_title = inlineformset_title

        # TODO: Review if these are still relevant.
        self.cms_app_title = cms_app_title
        self.cms_app_slug = cms_app_slug
        self.cms_app = cms_app

        # TODO: add an option to skip metadata creation


@python_2_unicode_compatible
class Wizard(WizardBase):
    template_name = 'cms/wizards/create.html'

    @property
    def id(self):
        content_type = ContentType.objects.get_for_model(self.get_model())
        return content_type.pk

    def __str__(self):
        # TODO: Is this legit? Is it even necessary?
        return self.title

    def get_success_url(self, obj, *args, **kwargs):
        # TODO: Review this comment for appropriateness.
        # We've decided the detail view is OK for some type of objects, so
        # default to it. Use language to redirect to a proper language version
        # of the object:
        if 'language' in kwargs:
            with force_language(kwargs['language']):
                return obj.get_absolute_url()
        else:
            return obj.get_absolute_url()

    def user_can_edit_object(self, obj, user):
        """Return True if object can be edited/deleted"""
        raise NotImplementedError

    def get_model(self):
        if self.model:
            return self.model
        if issubclass(self.form, ModelForm):
            return self.form._meta.model
        raise ImproperlyConfigured("Please set entry 'model' attribute or use"
                                   "ModelForm subclass as a form")

    # TODO: Is this necessary?
    def get_admin_model(self):
        if self.admin_model:
            return self.admin_model
        return self.get_model()

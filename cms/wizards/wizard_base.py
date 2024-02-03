import hashlib

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.translation import gettext as _, override as force_language

from cms.toolbar.utils import (
    get_object_edit_url,
    get_object_preview_url,
)


class WizardBase:
    """

    """
    template_name = None

    def __init__(self, title, weight, form, model=None, template_name=None,
                 description=None, edit_mode_on_success=True):
        """
        :param title: The title of the wizard. It will appear in a large font size on the wizard “menu”
        :param weight: Used for determining the order of the wizards on the
                       creation form.
        :param form: The form to use for this wizard. This is mandatory, but can
                     be sub-classed from :class:`django.forms.Form` or clas:`django.forms.ModelForm`.
        :param model: Required either here or in the form's Meta class. This is
                      used to determine uniqueness of the wizards, so, only one
                      wizard per model.
        :param template_name: The full-path to the template to use, if any.
        :param description: This is used on the start form. The description is optional, but if it is
                            not supplied, the CMS will create one from the pattern:
                            "Create a new «model.verbose_name» instance."
        :param edit_mode_on_success: Whether the user will get redirected to object edit url after a
                                     successful creation or not. This only works if the object is registered
                                     for toolbar enabled models.
        """
        self.title = title
        self.weight = weight
        self.form = form
        self.model = model
        self.description = description
        self.edit_mode_on_success = edit_mode_on_success
        if template_name is not None:
            self.template_name = template_name


class Wizard(WizardBase):
    """
     All wizard classes should inherit from ``cms.wizards.wizard_base.Wizard``. This
     class implements a number of methods that may be overridden as required.
     """

    template_name = 'cms/wizards/create.html'
    _hash_cache = None

    @property
    def id(self):
        """
        To construct a unique ID for each wizard, we start with the module and
        class name for uniqueness, we hash it because a wizard's ID is displayed
        in the form's markup, and we'd rather not expose code paths there.
        """
        if not self._hash_cache:
            full_path = force_str(
                ".".join([self.__module__, self.__class__.__name__])
            ).encode('utf-8')
            hash = hashlib.sha1()
            hash.update(full_path)
            self._hash_cache = hash.hexdigest()
        return self._hash_cache

    def get_title(self, **kwargs):
        """
        Simply returns the ``title`` property assigned during instantiation. Override
        this method if this needs to be determined programmatically.
        """
        return self.title

    def get_weight(self, **kwargs):
        """
        Simply returns the ``weight`` property assigned during instantiation. Override
        this method if this needs to be determined programmatically.
        """
        return self.weight

    def get_description(self, **kwargs):
        """
        Simply returns the ``description`` property assigned during instantiation or one
        derived from the model if description is not provided during instantiation.
        Override this method if this needs to be determined programmatically.
        """
        if self.description:
            return self.description

        model = self.get_model()
        if model:
            model_name = model._meta.verbose_name
            return _("Create a new %s instance.") % model_name

        return ""

    def __str__(self):
        return force_str(self.title)

    def __repr__(self):
        display = f'<{self.__module__}.{self.__class__.__name__} id={self.id} object at {hex(id(self))}>'
        return display

    def user_has_add_permission(self, user, **kwargs):
        """
        Returns boolean reflecting whether the given «user» has permission to
        add instances of this wizard's associated model. Can be overridden as
        required for more complex situations.

        :param user: The current user using the wizard.
        :return: True if the user should be able to use this wizard.
        """
        model = self.get_model()
        app_label = model._meta.app_label
        model_name = model.__name__.lower()
        return user.has_perm(f"{app_label}.add_{model_name}")

    def get_success_url(self, obj, **kwargs):
        """
        Once the wizard has completed, the user will be redirected to the URL of the new
        object that was created. By default, this is done by return the result of
        calling the ``get_absolute_url`` method on the object. If the object is registered
        for toolbar enabled models, the object edit url will be returned. This may be modified
        to return the preview url instead by setting the wizard property ``edit_mode_on_success``
        to False.

        In some cases, the created content will not implement ``get_absolute_url`` or
        that redirecting the user is undesirable. In these cases, simply override this
        method. If ``get_success_url`` returns ``None``, the CMS will just redirect to
        the current page after the object is created.

        :param object obj: The created object
        :param dict kwargs: Arbitrary keyword arguments
        """
        extension = apps.get_app_config('cms').cms_extension

        if obj.__class__ in extension.toolbar_enabled_models:
            if self.edit_mode_on_success:
                return get_object_edit_url(obj, language=kwargs.get("language", None))
            return get_object_preview_url(obj, language=kwargs.get("language", None))
        else:
            if "language" in kwargs:
                with force_language(language=kwargs["language"]):
                    return obj.get_absolute_url()
            return obj.get_absolute_url()

    def get_model(self):
        if self.model:
            return self.model
        if issubclass(self.form, ModelForm):
            model = self.form._meta.model
            if model:
                return model
        raise ImproperlyConfigured("Please set entry 'model' attribute or use "
                                   "ModelForm subclass as a form")

    @cached_property
    def widget_attributes(self):
        return {
            'description': self.get_description(),
            'title': self.get_title(),
            'weight': self.get_weight(),
            'id': self.id,
            'form': self.form,
            'model': self.model,
            'template_name': self.template_name
        }

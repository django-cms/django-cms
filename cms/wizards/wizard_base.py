import hashlib

from django.core.exceptions import ImproperlyConfigured
from django.forms.models import ModelForm
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import override as force_language

from cms.utils.conf import get_cms_setting


class WizardBase:
    template_name = None

    def __init__(self, title, weight, form, model=None, template_name=None,
                 description=None, edit_mode_on_success=True):
        """
        :param title: This is used on the start form.
        :param weight: Used for determining the order of the wizards on the
                       creation form.
        :param form: The form to use.
        :param model: Required either here or in the form's Meta class. This is
                      used to determine uniqueness of the wizards, so, only one
                      wizard per model.
        :param template_name: The full-path to the template to use, if any.
        :param description: This is used on the start form.
        :param edit_mode_on_success: If true, the CMS will switch to edit mode
                                     when going to the newly created object.
        """
        # NOTE: If class attributes or properties are changed, consider updating
        # cms.templatetags.cms_wizard_tags.WizardProperty too.
        self.title = title
        self.weight = weight
        self.form = form
        self.model = model
        self.description = description
        self.edit_mode_on_success = edit_mode_on_success
        if template_name is not None:
            self.template_name = template_name


class Wizard(WizardBase):
    template_name = 'cms/wizards/create.html'
    _hash_cache = None

    @property
    def id(self):
        """
        To construct an unique ID for each wizard, we start with the module and
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
        Return the title for this wizard. May be overridden as required.
        """
        return self.title

    def get_weight(self, **kwargs):
        """
        Return the weight for this wizard. May be overridden as required.
        """
        return self.weight

    def get_description(self, **kwargs):
        """
        Return the description for this wizard. May be overridden as required.
        """
        if self.description:
            return self.description

        model = self.get_model()
        if model:
            model_name = model._meta.verbose_name
            return _(u"Create a new %s instance.") % model_name

        return ""

    def __str__(self):
        return force_str(self.title)

    def __repr__(self):
        display = '<{module}.{class_name} id={id} object at {location}>'.format(
            module=self.__module__,
            class_name=self.__class__.__name__,
            id=self.id,
            location=hex(id(self)),
        )
        return display

    def user_has_add_permission(self, user, **kwargs):
        """
        Returns whether the given «user» has permission to add instances of this
        wizard's associated model. Can be overridden as required for more
        complex situations.

        :param user: The current user using the wizard.
        :return: True if the user should be able to use this wizard.
        """
        model = self.get_model()
        app_label = model._meta.app_label
        model_name = model.__name__.lower()
        return user.has_perm("%s.%s_%s" % (app_label, "add", model_name))

    def get_success_url(self, obj, **kwargs):
        """
        This should return the URL of the created object, «obj».
        """
        if 'language' in kwargs:
            with force_language(kwargs['language']):
                url = obj.get_absolute_url()
        else:
            url = obj.get_absolute_url()

        # Add 'edit' to GET params of URL
        if self.edit_mode_on_success:
            sep = "&" if "?" in url else "?"
            url = '{0}{1}{2}'.format(
                url, sep, get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON'))
        return url

    def get_model(self):
        if self.model:
            return self.model
        if issubclass(self.form, ModelForm):
            model = self.form._meta.model
            if model:
                return model
        raise ImproperlyConfigured(u"Please set entry 'model' attribute or use "
                                   u"ModelForm subclass as a form")

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

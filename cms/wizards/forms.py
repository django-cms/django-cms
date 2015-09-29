# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext as _

from cms.models import Page

from .wizard_pool import wizard_pool


def entry_choices(user):
    """
    Yields a list of wizard entries that the current user can use based on their
    permission to add instances of the underlying model objects.
    """
    for entry in wizard_pool.get_entries():
        if entry.user_has_add_permission(user):
            yield (entry.id, entry.title)


def step2_form_factory(mixin_cls, entry_form_class, attrs=None):
    """
    Combines a form mixin with a form class, sets attrs to the resulting class.
    This is used to provide a common behavior/logic for all wizard content
    forms.
    """
    if attrs is None:
        attrs = {}

    # class name is hardcoded to be consistent with the step 1 form.
    # this is meant to be used only in the context of the form wizard.
    class_name = 'WizardStep2Form'
    meta_class = type(entry_form_class)
    FormClass = meta_class(class_name, (mixin_cls, entry_form_class), attrs)
    return FormClass


class BaseFormMixin(object):
    has_separate_optional_fields = False

    def __init__(self, *args, **kwargs):
        self.page = kwargs.pop('wizard_page', None)
        self.user = kwargs.pop('wizard_user', None)
        # This goes into a fake form data in clean() and is also used
        # in a view to create objects in proper language.
        # We have no use case for empty language_code yet, so it is required.
        self.language_code = kwargs.pop('wizard_language')
        self.app_config = kwargs.pop('wizard_app_config', None)
        super(BaseFormMixin, self).__init__(*args, **kwargs)

    @property
    def required_fields(self):
        return [f for f in self.visible_fields() if f.field.required]

    @property
    def optional_fields(self):
        return [f for f in self.visible_fields() if not f.field.required]


class WizardStep1Form(BaseFormMixin, forms.Form):
    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=forms.HiddenInput
    )
    entry = forms.ChoiceField(choices=[], widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        self.user = kwargs['wizard_user']
        super(WizardStep1Form, self).__init__(*args, **kwargs)
        # set the entries here to get an up to date list of entries.
        self.fields['entry'].choices = entry_choices(user=self.user)

    def clean(self):
        page = self.cleaned_data.get('page')
        space = self.cleaned_data.get('space')

        invalid_request_message = _(u"We're unable to process your request.")

        if page and space:
            if page.application_urls:
                # user is creating an object for an apphooked page.
                raise forms.ValidationError(invalid_request_message)

            else:
                # user is creating an object for a page outside of space.
                raise forms.ValidationError(invalid_request_message)
        return self.cleaned_data


class WizardStep2BaseForm(BaseFormMixin):
    # Step two allows for inline formsets
    # so this attribute will point to an inline formset instance
    # only when user reaches step two.
    inlineformset = None
    user = None

    def is_valid(self):
        _is_valid = super(WizardStep2BaseForm, self).is_valid()

        if self.inlineformset:
            # if the form has an inlineformset
            # make sure both form and inlineformset are valid.
            _is_valid = _is_valid and self.inlineformset.is_valid()
        return _is_valid

    def save(self, **kwargs):
        instance = super(WizardStep2BaseForm, self).save(**kwargs)

        if self.inlineformset:
            # make sure to point to the new object
            self.inlineformset.instance = instance
            self.inlineformset.save()

        return instance

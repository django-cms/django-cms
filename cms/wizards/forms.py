# -*- coding: utf-8 -*-
from django import forms
from django.utils.html import format_html, force_text
from django.utils.safestring import mark_safe

from cms.models import Page
from cms.utils.compat import DJANGO_1_10
from cms.utils.urlutils import static_with_version

from .wizard_pool import entry_choices, wizard_pool


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
        self.language_code = kwargs.pop('wizard_language')
        super(BaseFormMixin, self).__init__(*args, **kwargs)

    @property
    def required_fields(self):
        return [f for f in self.visible_fields() if f.field.required]

    @property
    def optional_fields(self):
        return [f for f in self.visible_fields() if not f.field.required]


class WizardOptionWidgets(forms.RadioSelect):
    if DJANGO_1_10:
        class WizardOptionRenderer(forms.widgets.RadioFieldRenderer):
            class WizardOptionInput(forms.widgets.RadioChoiceInput):

                def __init__(self, name, value, attrs, choice, index):
                    super(WizardOptionWidgets.WizardOptionRenderer.WizardOptionInput, self).__init__(
                        name, value, attrs, choice, index
                    )
                    try:
                        wizard = wizard_pool.get_entry(choice[0])
                        self.label = force_text(choice[1])
                        self.description = wizard.widget_attributes['description']
                    except (ValueError, KeyError):
                        pass

                def __str__(self):
                    return self.render()

                def is_checked(self):
                    return self.index == 0

                def render(self, name=None, value=None, attrs=None):
                    attrs = dict(self.attrs, **attrs) if attrs else self.attrs
                    return format_html(
                        '<label tabindex="0" class="choice{active_class}">{tag}<strong>{label}</strong>'
                        '<span class="info">{description}</span></label>', **{
                            'tag': self.tag(attrs), 'label': self.label, 'description': self.description,
                            'active_class': ' active' if self.is_checked() else ''
                        }
                    )

            outer_html = '{content}'
            inner_html = '{choice_value}{sub_widgets}'
            choice_input_class = WizardOptionInput

            def render(self):
                """
                Outputs a <ul> for this set of choice fields.
                If an id was given to the field, it is applied to the <ul> (each
                item in the list will get an id of `$id_$i`).
                """
                id_ = self.attrs.get('id')
                output = []
                for i, choice in enumerate(self.choices):
                    w = self.choice_input_class(self.name, self.value, self.attrs.copy(), choice, i)
                    output.append(format_html(self.inner_html, choice_value='', sub_widgets=w.render()))
                return format_html(
                    self.outer_html,
                    id_attr=format_html(' id="{}"', id_) if id_ else '',
                    content=mark_safe('\n'.join(output)),
                )

        renderer = WizardOptionRenderer
    template_name = 'cms/wizards/wizardoptionwidget.html'

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        try:
            wizard = wizard_pool.get_entry(value)
            attrs.update(wizard.widget_attributes)
        except ValueError:
            pass
        return super(WizardOptionWidgets, self).create_option(name, value, label, selected, index, subindex, attrs)


class WizardStep1Form(BaseFormMixin, forms.Form):

    class Media:
        css = {
            'all': (
                static_with_version('cms/css/cms.wizard.css'),
            )
        }
        js = (
            static_with_version('cms/js/dist/bundle.admin.base.min.js'),
            'cms/js/modules/cms.wizards.js',
        )

    page = forms.ModelChoiceField(
        queryset=Page.objects.all(),
        required=False,
        widget=forms.HiddenInput
    )
    language = forms.CharField(widget=forms.HiddenInput)
    entry = forms.ChoiceField(choices=[], widget=WizardOptionWidgets())

    def __init__(self, *args, **kwargs):
        super(WizardStep1Form, self).__init__(*args, **kwargs)
        # set the entries here to get an up to date list of entries.
        self.fields['entry'].choices = entry_choices(user=self.user,
                                                     page=self.page)


class WizardStep2BaseForm(BaseFormMixin):
    user = None

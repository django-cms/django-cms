# -*- coding: utf-8 -*-

import os

from django.forms import Form
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import NoReverseMatch
from django.template.response import SimpleTemplateResponse

from formtools.wizard.views import SessionWizardView

from cms.models import Page
from cms.utils import get_current_site
from cms.utils.compat import DJANGO_1_10
from cms.utils.i18n import get_site_language_from_request

from .wizard_pool import wizard_pool
from .forms import (
    WizardStep1Form,
    WizardStep2BaseForm,
    step2_form_factory,
)


class WizardCreateView(SessionWizardView):
    template_name = 'cms/wizards/start.html'
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'wizard_tmp_files'))

    form_list = [
        ('0', WizardStep1Form),
        # Form is used as a placeholder form.
        # the real form will be loaded after step 0
        ('1', Form),
    ]

    def dispatch(self, *args, **kwargs):
        user = self.request.user

        if not user.is_active or not user.is_staff:
            raise PermissionDenied
        self.site = get_current_site()
        return super(WizardCreateView, self).dispatch(*args, **kwargs)

    def get_current_step(self):
        """Returns the current step, if possible, else None."""
        try:
            return self.steps.current
        except AttributeError:
            return None

    def is_first_step(self, step=None):
        step = step or self.get_current_step()
        return step == '0'

    def is_second_step(self, step=None):
        step = step or self.get_current_step()
        return step == '1'

    def get_context_data(self, **kwargs):
        context = super(WizardCreateView, self).get_context_data(**kwargs)

        if self.is_first_step():
            context['DJANGO_1_10'] = DJANGO_1_10

        if self.is_second_step():
            context['wizard_entry'] = self.get_selected_entry()
        return context

    def get_form(self, step=None, data=None, files=None):
        if step is None:
            step = self.steps.current

        # We need to grab the page from pre-validated data so that the wizard
        # has it to prepare the list of valid entries.
        if data:
            page_key = "{0}-page".format(step)
            self.page_pk = data.get(page_key, None)
        else:
            self.page_pk = None

        if self.is_second_step(step):
            self.form_list[step] = self.get_step_2_form(step, data, files)
        return super(WizardCreateView, self).get_form(step, data, files)

    def get_form_kwargs(self, step=None):
        """This is called by self.get_form()"""
        kwargs = super(WizardCreateView, self).get_form_kwargs()
        kwargs['wizard_user'] = self.request.user
        if self.is_second_step(step):
            kwargs['wizard_page'] = self.get_origin_page()
            kwargs['wizard_language'] = self.get_origin_language()
        else:
            page_pk = self.page_pk or self.request.GET.get('page', None)
            if page_pk and page_pk != 'None':
                kwargs['wizard_page'] = Page.objects.filter(pk=page_pk).first()
            else:
                kwargs['wizard_page'] = None
            kwargs['wizard_language'] = get_site_language_from_request(
                self.request,
                site_id=self.site.pk,
            )
        return kwargs

    def get_form_initial(self, step):
        """This is called by self.get_form()"""
        initial = super(WizardCreateView, self).get_form_initial(step)
        if self.is_first_step(step):
            initial['page'] = self.request.GET.get('page')
            initial['language'] = self.request.GET.get('language')
        return initial

    def get_step_2_form(self, step=None, data=None, files=None):
        entry_form_class = self.get_selected_entry().form
        step_2_base_form = self.get_step_2_base_form()

        form = step2_form_factory(
            mixin_cls=step_2_base_form,
            entry_form_class=entry_form_class,
        )
        return form

    def get_step_2_base_form(self):
        """
        Returns the base form to be used for step 2.
        This form is sub classed dynamically by the form defined per module.
        """
        return WizardStep2BaseForm

    def get_template_names(self):
        if self.is_first_step():
            template_name = self.template_name
        else:
            template_name = self.get_selected_entry().template_name
        return template_name

    def done(self, form_list, **kwargs):
        """
        This step only runs if all forms are valid. Simply emits a simple
        template that uses JS to redirect to the newly created object.
        """
        form_one, form_two = list(form_list)
        instance = form_two.save()
        url = self.get_success_url(instance)
        language = form_one.cleaned_data['language']
        if not url:
            page = self.get_origin_page()
            if page:
                try:
                    url = page.get_absolute_url(language)
                except NoReverseMatch:
                    url = '/'
            else:
                url = '/'

        return SimpleTemplateResponse("cms/wizards/done.html", {"url": url})

    def get_selected_entry(self):
        data = self.get_cleaned_data_for_step('0')
        return wizard_pool.get_entry(data['entry'])

    def get_origin_page(self):
        data = self.get_cleaned_data_for_step('0')
        return data.get('page')

    def get_origin_language(self):
        data = self.get_cleaned_data_for_step('0')
        return data.get('language')

    def get_success_url(self, instance):
        entry = self.get_selected_entry()
        language = self.get_origin_language()
        success_url = entry.get_success_url(
            obj=instance,
            language=language,
        )
        return success_url

# -*- coding: utf-8 -*-
from cms import constants
from cms.api import create_page
from cms.utils.permissions import has_page_add_permission
from django import forms
from django.conf import settings
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.views import login
from django.core.urlresolvers import resolve, Resolver404
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.template import RequestContext
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _, \
    get_language_from_request

from cms.cache.page import set_page_cache
from cms.models import Page
from cms.utils import get_template_from_request, get_cms_setting


def render_page(request, page, current_language, slug):
    """
    Renders a page
    """
    template_name = get_template_from_request(request, page, no_current_page=True)
    # fill the context
    context = RequestContext(request)
    context['lang'] = current_language
    context['current_page'] = page
    context['has_change_permissions'] = page.has_change_permission(request)
    context['has_view_permissions'] = page.has_view_permission(request)

    if not context['has_view_permissions']:
        return _handle_no_page(request, slug)

    response = TemplateResponse(request, template_name, context)

    response.add_post_render_callback(set_page_cache)

    # Add headers for X Frame Options - this really should be changed upon
    # moving to class based views
    xframe_options = page.get_xframe_options()
    # xframe_options can be None if there's no xframe information on the page
    # (eg. a top-level page which has xframe options set to "inherit")
    if xframe_options == Page.X_FRAME_OPTIONS_INHERIT or xframe_options is None:
        # This is when we defer to django's own clickjacking handling
        return response

    # We want to prevent django setting this in their middlewear
    response.xframe_options_exempt = True

    if xframe_options == Page.X_FRAME_OPTIONS_ALLOW:
        # Do nothing, allowed is no header.
        return response
    elif xframe_options == Page.X_FRAME_OPTIONS_SAMEORIGIN:
        response['X-Frame-Options'] = 'SAMEORIGIN'
    elif xframe_options == Page.X_FRAME_OPTIONS_DENY:
        response['X-Frame-Options'] = 'DENY'
    return response


class SimpleAddPageForm(forms.Form):
    title = forms.CharField(label=_("Title"), widget=forms.TextInput(),
                            help_text=_('Title of your home page'))

    def save(self, template, language, user):
        return create_page(
            title=self.cleaned_data['title'],
            language=language,
            template=template,
            created_by=user,
        )


def welcome(request):
    if not request.user.is_authenticated():
        response = login(
            request,
            authentication_form=AdminAuthenticationForm,
            template_name='cms/welcome_login.html'
        )
        if request.user.is_authenticated():
            return HttpResponseRedirect(request.path)
        else:
            return response
    else:
        config_errors = []
        templates = get_cms_setting('TEMPLATES')
        if (len(templates) == 0 and
                templates[0] == constants.TEMPLATE_INHERITANCE_MAGIC):
            config_errors.append(_("You must configure CMS_TEMPLATES"))
        if not has_page_add_permission(request):
            config_errors.append(_("You do not have permission to add a page"))
            can_save = False
        else:
            can_save = True
        if request.method == 'POST':
            form = SimpleAddPageForm(request.POST)
            if form.is_valid() and can_save:
                language = get_language_from_request(request)
                page = form.save(
                    templates[0][0],
                    language,
                    request.user,
                )
                return HttpResponseRedirect('{path}?{flag}'.format(
                    path=page.get_absolute_url(language=language),
                    flag=get_cms_setting('TOOLBAR_URL__EDIT_ON')
                ))
        else:
            form = SimpleAddPageForm()
        context = {
            'form': form,
            'config_errors': config_errors
        }
        return render(request, 'cms/welcome.html', context)


def _handle_no_page(request, slug):
    if not slug and settings.DEBUG:
        return welcome(request)
    try:
        # add a $ to the end of the url (does not match on the cms anymore)
        resolve('%s$' % request.path)
    except Resolver404 as e:
        # raise a django http 404 page
        exc = Http404(dict(path=request.path, tried=e.args[0]['tried']))
        raise exc
    raise Http404('CMS Page not found: %s' % request.path)


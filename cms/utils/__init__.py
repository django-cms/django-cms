# TODO: this is just stuff from utils.py - should be splitted / moved
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse

from cms.utils.i18n import get_default_language
import urllib

# !IMPORTANT: Page cant be imported here, because we will get cyclic import!!

def auto_render(func):
    """Decorator that put automaticaly the template path in the context dictionary
    and call the render_to_response shortcut"""
    def _dec(request, *args, **kwargs):
        t = None
        if kwargs.get('only_context', False):
            # return only context dictionary
            del(kwargs['only_context'])
            response = func(request, *args, **kwargs)
            if isinstance(response, HttpResponse):
                return response
            (template_name, context) = response
            return context
        if "template_name" in kwargs:
            t = kwargs['template_name']
            del kwargs['template_name']
        response = func(request, *args, **kwargs)
        if isinstance(response, HttpResponse):
            return response
        (template_name, context) = response
        if not t:
            t = template_name
        context['template_name'] = t
        return render_to_response(t, context, context_instance=RequestContext(request))
    return _dec

def get_template_from_request(request, obj=None, no_current_page=False):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    template = None
    if len(settings.CMS_TEMPLATES) == 1:
        return settings.CMS_TEMPLATES[0][0]
    if "template" in request.REQUEST:
        template = request.REQUEST['template']
    if not template and obj is not None:
        template = obj.get_template()
    if not template and not no_current_page and hasattr(request, "current_page"):
        current_page = request.current_page
        if hasattr(current_page, "get_template"):
            template = current_page.get_template()
    if template is not None and template in dict(settings.CMS_TEMPLATES).keys():
        if template == settings.CMS_TEMPLATE_INHERITANCE_MAGIC and obj:
            # Happens on admin's request when changing the template for a page
            # to "inherit".
            return obj.get_template()
        return template    
    return settings.CMS_TEMPLATES[0][0]


def get_language_from_request(request, current_page=None):
    from cms.models import Page
    """
    Return the most obvious language according the request
    """
    if settings.CMS_DBGETTEXT: 
        return get_default_language()
    language = request.REQUEST.get('language', None)
    if language:
        if not language in dict(settings.CMS_LANGUAGES).keys():
            language = None
    if language is None:
        language = getattr(request, 'LANGUAGE_CODE', None)
    if language:
        if not language in dict(settings.CMS_LANGUAGES).keys():
            language = None

    # TODO: This smells like a refactoring oversight - was current_page ever a page object? It appears to be a string now
    if language is None and isinstance(current_page, Page):
        # in last resort, get the first language available in the page
        languages = current_page.get_languages()

        if len(languages) > 0:
            language = languages[0]

    if language is None:
        # language must be defined in CMS_LANGUAGES, so check first if there
        # is any language with LANGUAGE_CODE, otherwise try to split it and find
        # best match
        language = get_default_language()

    return language


def get_page_from_request(request):
    """
    tries to get a page from a request if the page hasn't been handled by the cms urls.py
    """

    # TODO: Looks redundant this is also checked in cms.middleware.page and thats the only place this method get called
    if hasattr(request, '_current_page_cache'):
        return request._current_page_cache
    else:
        path = request.path
        from cms.views import details
        
        kw = {}
        # TODO: very ugly - change required!
        
        if path.startswith('/admin/'):
            kw['page_id']=path.split("/")[0]
        else:
            pages_root = urllib.unquote(reverse("pages-root"))
            kw['slug']=path[len(pages_root):-1]
        resp = details(request, no404=True, only_context=True, **kw)
        return resp['current_page']


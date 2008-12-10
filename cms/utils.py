from django.shortcuts import render_to_response
from django.template import RequestContext

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.sites.models import Site, RequestSite, SITE_CACHE

from cms import settings

def auto_render(func):
    """Decorator that put automaticaly the template path in the context dictionary
    and call the render_to_response shortcut"""
    def _dec(request, *args, **kwargs):
        t = None
        if kwargs.get('only_context', False):
            # return only context dictionary
            del(kwargs['only_context'])
            response = func(request, *args, **kwargs)
            if isinstance(response, HttpResponse) or isinstance(response, HttpResponseRedirect):
                raise Except("cannot return context dictionary because a HttpResponseRedirect as been found")
            (template_name, context) = response
            return context
        if "template_name" in kwargs:
            t = kwargs['template_name']
            del kwargs['template_name']
        response = func(request, *args, **kwargs)
        if isinstance(response, HttpResponse) or isinstance(response, HttpResponseRedirect):
            return response
        (template_name, context) = response
        if not t:
            t = template_name
        context['template_name'] = t
        return render_to_response(t, context, context_instance=RequestContext(request))
    return _dec

def get_template_from_request(request, obj=None):
    """
    Gets a valid template from different sources or falls back to the default
    template.
    """
    if settings.CMS_TEMPLATES is None:
        return settings.DEFAULT_CMS_TEMPLATE
    template = request.REQUEST.get('template', None)
    if template is not None and \
            template in dict(settings.CMS_TEMPLATES).keys():
        return template
    if obj is not None:
        return obj.get_template()
    return settings.DEFAULT_CMS_TEMPLATE

def get_language_in_settings(iso):
    for language in settings.CMS_LANGUAGES:
        if language[0][:2] == iso:
            return iso
    return None

def get_language_from_request(request, current_page=None):
    """
    Return the most obvious language according the request
    """
    language = get_language_in_settings(request.REQUEST.get('language', None))
    if language is None:
        language = getattr(request, 'LANGUAGE_CODE', None)
    if language is None:
        # in last resort, get the first language available in the page
        if current_page:
            languages = current_page.get_languages()
            if len(languages) > 0:
                language = languages[0]
    if language is None:
        language = settings.CMS_DEFAULT_LANGUAGE
    return language[:2]

def has_page_add_permission(request, page=None):
    """
    Return true if the current user has permission to add a new page.
    """
    if not settings.CMS_PERMISSION:
        return True
    else:
        from cms.models import PagePermission
        permission = PagePermission.objects.get_edit_id_list(request.user)
        if permission == "All":
            return True
    return False

def get_site_from_request(request, check_subdomain=True):
    """
    Returns the ``Site`` which matches the host name retreived from
    ``request``.

    If no match is found and ``check_subdomain`` is ``True``, the sites are
    searched again for sub-domain matches.

    If still no match, or if more than one ``Site`` matched the host name, a
    ``RequestSite`` object is returned.

    The returned ``Site`` or ``RequestSite`` object is cached for the host
    name retrieved from ``request``.
    """ 
    host = request.get_host().lower()
    if host in SITE_CACHE:
        # The host name was found in cache, return it. A cache value
        # of None means that a RequestSite should just be used.
        return SITE_CACHE[host] or RequestSite(request)
    matches = Site.objects.filter(domain__iexact=host)
    # We use len rather than count to save a second query if there was only
    # one matching Site
    count = len(matches)
    if not count and check_subdomain:
        matches = []
        for site in Site.objects.all():
            if host.endswith(site.domain.lower()):
                matches.append(site)
        count = len(matches)
    if count == 1:
        # Return the single matching Site
        site = matches[0]
    else:
        site = None
    # Cache the site (caching None means we should use RequestSite).
    SITE_CACHE[host] = site
    # Return site, falling back to just using a RequestSite.
    return site or RequestSite(request)

def get_page_from_request(request):
    return request['current_page']



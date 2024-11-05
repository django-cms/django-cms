from collections import OrderedDict
from importlib import import_module

from django.core.exceptions import ImproperlyConfigured
from django.db import OperationalError, ProgrammingError
from django.urls import NoReverseMatch, Resolver404, URLResolver, reverse
from django.urls.resolvers import RegexPattern, URLPattern
from django.utils.translation import get_language, override

from cms.apphook_pool import apphook_pool
from cms.models.pagemodel import Page
from cms.utils import get_current_site
from cms.utils.i18n import get_language_list

APP_RESOLVERS = []


def clear_app_resolvers():
    global APP_RESOLVERS
    APP_RESOLVERS = []


def applications_page_check(request):
    """Tries to find if given path was resolved over application.
    Applications have higher priority than other cms pages.
    """
    # We should get in this branch only if an apphook is active on /
    # This removes the non-CMS part of the URL.
    try:
        path = request.path_info.replace(reverse('pages-root'), '', 1)
    except NoReverseMatch:
        path = request.path_info

    # check if application resolver can resolve this
    for lang in get_language_list():
        if path.startswith(lang + "/"):
            path = path[len(lang + "/"):]

    for resolver in APP_RESOLVERS:
        try:
            page_id = resolver.resolve_page_id(path)
            return Page.objects.get(id=page_id)
        except Resolver404:
            # Raised if the page is not managed by an apphook
            pass
        except Page.DoesNotExist:
            pass
    return None


class AppRegexURLResolver(URLResolver):
    def __init__(self, *args, **kwargs):
        self.page_id = None
        self.url_patterns_dict = {}
        super().__init__(*args, **kwargs)

    @property
    def urlconf_module(self):
        # It is valid for urlconf_module to be a list of patterns. So we just
        # return the list here.
        #
        # See https://github.com/django/django/blob/2.2.4/django/urls/resolvers.py#L578
        #
        return self.url_patterns_dict.get(get_language(), [])

    # On URLResolver the url_patterns property is cached and thus calls made after
    # language changes (different return values for get_language()) would not return the
    # right value. Overriding here prevents caching.
    @property
    def url_patterns(self):
        return self.urlconf_module

    def resolve_page_id(self, path):
        """Resolves requested path similar way how resolve does, but instead
        of return callback,.. returns page_id to which was application
        assigned.
        """
        tried = []
        pattern = getattr(self, 'pattern', self)
        match = pattern.regex.search(path)
        if match:
            new_path = path[match.end():]
            for pattern in self.url_patterns:
                if isinstance(pattern, AppRegexURLResolver):
                    try:
                        return pattern.resolve_page_id(new_path)
                    except Resolver404:
                        pass
                else:
                    try:
                        sub_match = pattern.resolve(new_path)
                    except Resolver404 as e:
                        tried_match = e.args[0].get('tried')
                        if tried_match is not None:
                            tried.extend([[pattern] + t for t in tried_match])
                        else:
                            tried.extend([pattern])
                    else:
                        if sub_match:
                            return getattr(pattern, 'page_id', None)
                        pattern = getattr(pattern, 'pattern', pattern)
                        tried.append(pattern.regex.pattern)
            raise Resolver404({'tried': tried, 'path': new_path})


def recurse_patterns(path, pattern_list, page_id, default_args=None,
                     nested=False):
    """
    Recurse over a list of to-be-hooked patterns for a given path prefix
    """
    newpatterns = []
    for pattern in pattern_list:
        app_pat = getattr(pattern, 'pattern', pattern).regex.pattern
        # make sure we don't get patterns that start with more than one '^'!
        app_pat = app_pat.lstrip('^')
        path = path.lstrip('^')
        regex = rf'^{path}{app_pat}' if not nested else r'^%s' % (app_pat)
        if isinstance(pattern, URLResolver):
            # include default_args
            args = pattern.default_kwargs
            if default_args:
                args.update(default_args)
            # see lines 243 and 236 of urlresolvers.py to understand the next line
            urlconf_module = recurse_patterns(regex, pattern.url_patterns, page_id, args, nested=True)
            # this is an 'include', recurse!
            regex_pattern = regex
            regex_pattern = RegexPattern(regex)
            resolver = URLResolver(regex_pattern, urlconf_module,
                                   pattern.default_kwargs, pattern.app_name,
                                   pattern.namespace)
        else:
            # Re-do the URLPattern with the new regular expression
            args = pattern.default_args
            if default_args:
                args.update(default_args)

            regex_pattern = RegexPattern(regex, name=pattern.name, is_endpoint=True)
            resolver = URLPattern(regex_pattern, pattern.callback, args,
                                  pattern.name)
        resolver.page_id = page_id
        newpatterns.append(resolver)
    return newpatterns


def _set_permissions(patterns, exclude_permissions):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            if pattern.namespace in exclude_permissions:
                continue
            _set_permissions(pattern.url_patterns, exclude_permissions)
        else:
            from cms.utils.decorators import cms_perms
            pattern.callback = cms_perms(pattern.callback)


def get_app_urls(urls):
    for urlconf in urls:
        if isinstance(urlconf, str):
            mod = import_module(urlconf)
            if not hasattr(mod, 'urlpatterns'):
                raise ImproperlyConfigured(
                    "URLConf `%s` has no urlpatterns attribute" % urlconf)
            yield mod.urlpatterns
        elif isinstance(urlconf, (list, tuple)):
            yield urlconf
        else:
            yield [urlconf]


def get_patterns_for_page_url(page_url):
    """
    Resolve the urlconf module for a path+title combination
    Returns a list of url objects.
    """
    path = page_url.path

    if path and not path.endswith('/'):
        path += '/'

    app = apphook_pool.get_apphook(page_url.page.application_urls)

    url_patterns = []
    for pattern_list in get_app_urls(app.get_urls(page_url.page, page_url.language)):
        url_patterns += recurse_patterns(path, pattern_list, page_url.page_id)
    return url_patterns


def get_app_patterns():
    try:
        site = get_current_site()
        return _get_app_patterns(site)
    except (OperationalError, ProgrammingError):
        # ignore if DB is not ready
        # Starting with Django 1.9 this code gets called even when creating
        # or running migrations. So in many cases the DB will not be ready yet.
        return []


def _get_app_patterns(site):
    """
    Get a list of patterns for all hooked apps.

    How this works:

    By looking through all titles with an app hook (application_urls) we find
    all urlconf modules we have to hook into titles.

    If we use the ML URL Middleware, we namespace those patterns with the title
    language.

    All 'normal' patterns from the urlconf get re-written by prefixing them with
    the title path and then included into the cms url patterns.

    If the app is still configured, but is no longer installed/available, then
    this method returns a degenerate patterns object: patterns('')
    """
    from cms.models.pagemodel import PageUrl

    included = []
    hooked_applications = OrderedDict()

    # we don't have a request here so get_page_queryset() can't be used,
    # so use public() queryset.
    # This can be done because url patterns are used just in frontend
    page_urls = PageUrl.objects.get_for_site(site)

    # Loop over all titles with an application hooked to them
    page_urls = (
        page_urls
        .exclude(page__application_urls=None)
        .exclude(page__application_urls='')
        .order_by('-page__path')
        .select_related('page')
    )

    for page_url in page_urls:
        mix_id = "{}:{}:{}".format(
            page_url.path + "/",
            page_url.page.application_urls,
            page_url.language,
        )

        if mix_id in included:
            # don't add the same thing twice
            continue
        app = apphook_pool.get_apphook(page_url.page.application_urls)
        if not app:
            continue
        if page_url.page_id not in hooked_applications:
            hooked_applications[page_url.page_id] = {}
        app_ns = app.app_name, page_url.page.application_namespace
        with override(page_url.language):
            hooked_applications[page_url.page_id][page_url.language] = (
                app_ns, get_patterns_for_page_url(page_url), app)
        included.append(mix_id)
        # Build the app patterns to be included in the cms urlconfs
    app_patterns = []
    for page_id in hooked_applications.keys():
        resolver = None
        for lang in hooked_applications[page_id].keys():
            (app_ns, inst_ns), current_patterns, app = hooked_applications[page_id][lang]  # nopyflakes
            if not resolver:
                regex_pattern = RegexPattern(r'')
                resolver = AppRegexURLResolver(
                    regex_pattern, 'app_resolver', app_name=app_ns, namespace=inst_ns)
                resolver.page_id = page_id
            if app.permissions:
                _set_permissions(current_patterns, app.exclude_permissions)

            resolver.url_patterns_dict[lang] = current_patterns
        app_patterns.append(resolver)
        APP_RESOLVERS.append(resolver)
    return app_patterns

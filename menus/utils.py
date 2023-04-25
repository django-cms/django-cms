from django.conf import settings
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from cms.utils import get_current_site, get_language_from_request
from cms.utils.i18n import (
    force_language,
    get_default_language_for_site,
    get_fallback_languages,
    hide_untranslated,
    is_valid_site_language,
)


def mark_descendants(nodes):
    for node in nodes:
        node.descendant = True
        mark_descendants(node.children)


def cut_levels(nodes, level):
    """
    For cutting the nav_extender levels if you have a from_level in the navigation.
    """
    if nodes:
        if nodes[0].level == level:
            return nodes
    return sum((cut_levels(node.children, level) for node in nodes), [])


def find_selected(nodes):
    """
    Finds a selected nav_extender node
    """
    for node in nodes:
        if hasattr(node, "selected"):
            return node
        elif hasattr(node, "ancestor"):
            result = find_selected(node.children)
            if result:
                return result


def set_language_changer(request, func):
    """
    Sets a language chooser function that accepts one parameter: language
    The function should return a url in the supplied language
    normally you would want to give it the get_absolute_url function with an optional language parameter
    example:

    def get_absolute_url(self, language=None):
        reverse('product_view', args=[self.get_slug(language=language)])

    Use this function in your nav extender views that have i18n slugs.
    """
    request._language_changer = func


def language_changer_decorator(language_changer):
    """
    A decorator wrapper for set_language_changer.

        from menus.utils import language_changer_decorator

        @language_changer_decorator(function_get_language_changer_url)
        def my_view_function(request, somearg):
            pass
    """
    def _decorator(func):
        def _wrapped(request, *args, **kwargs):
            set_language_changer(request, language_changer)
            return func(request, *args, **kwargs)
        _wrapped.__name__ = func.__name__
        _wrapped.__doc__ = func.__doc__
        return _wrapped
    return _decorator


class DefaultLanguageChanger:
    def __init__(self, request):
        self.request = request
        self._app_path = None

    @property
    def app_path(self):
        if self._app_path is None:
            if settings.USE_I18N:
                page_path = self.get_page_path(get_language_from_request(self.request))
            else:
                page_path = self.get_page_path(settings.LANGUAGE_CODE)
            if page_path:
                self._app_path = self.request.path_info[len(page_path):]
            else:
                self._app_path = self.request.path_info
        return self._app_path

    def get_page_path(self, lang):
        page = getattr(self.request, 'current_page', None)

        if not page:
            return '/%s/' % lang if settings.USE_I18N else '/'

        page_languages = page.get_published_languages()

        if lang in page_languages:
            return page.get_absolute_url(lang, fallback=False)

        site = get_current_site()

        if is_valid_site_language(lang, site_id=site.pk):
            _valid_language = True
            _hide_untranslated = hide_untranslated(lang, site.pk)
        else:
            _valid_language = False
            _hide_untranslated = False

        if _hide_untranslated and settings.USE_I18N:
            return '/%s/' % lang

        default_language = get_default_language_for_site(site.pk)

        if not _valid_language and default_language in page_languages:
            # The request language is not configured for the current site.
            # Fallback to the default language configured for the current site.
            return page.get_absolute_url(default_language, fallback=False)

        if _valid_language:
            fallbacks = get_fallback_languages(lang, site_id=site.pk) or []
            fallbacks = [_lang for _lang in fallbacks if _lang in page_languages]
        else:
            fallbacks = []

        if fallbacks:
            return page.get_absolute_url(fallbacks[0], fallback=False)
        return '/%s/' % lang if settings.USE_I18N else '/'

    def __call__(self, lang):
        page_language = get_language_from_request(self.request)
        with force_language(page_language):
            try:
                view = resolve(self.request.path_info)
            except Resolver404:
                view = None
        if hasattr(self.request, 'toolbar') and self.request.toolbar.obj:
            with force_language(lang):
                try:
                    return self.request.toolbar.obj.get_absolute_url()
                except:  # noqa: E722
                    pass
        elif view and view.url_name not in ('pages-details-by-slug', 'pages-root'):
            view_name = view.url_name
            if view.namespace:
                view_name = "%s:%s" % (view.namespace, view_name)
            url = None
            with force_language(lang):
                try:
                    url = reverse(view_name, args=view.args, kwargs=view.kwargs, current_app=view.app_name)
                except NoReverseMatch:
                    pass
            if url:
                return url
        return '%s%s' % (self.get_page_path(lang), self.app_path)

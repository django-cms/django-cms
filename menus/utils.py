from django.conf import settings
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from cms.toolbar.utils import get_object_edit_url, get_object_for_language, get_object_preview_url
from cms.utils import get_current_site, get_language_from_request
from cms.utils.i18n import (
    force_language,
    get_default_language_for_site,
    get_fallback_languages,
    hide_untranslated,
    is_valid_site_language,
)


def mark_descendants(nodes):
    """
    Mark the descendants of each node in a list.

    Args:
        nodes (list): A list of nodes.

    Returns:
        None

    Modifies:
        Each node in the input list will have its `descendant` attribute set to True.

    Note:
        This function is a recursive function that marks the descendants of each node in the input list.

    Raises:
        None
    """
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
    Sets a language chooser function that accepts one parameter: language.

    Parameters:
    language (str): The language to be used.

    Returns:
    str: The URL in the supplied language.

    Example:
        def get_absolute_url(self, language=None):
            reverse('product_view', args=[self.get_slug(language=language)])

    Use this function in your nav extender views that have i18n slugs.
    """
    request._language_changer = func


def language_changer_decorator(language_changer):
    """
    A decorator wrapper for set_language_changer.

    Example usage:

        from menus.utils import language_changer_decorator

        @language_changer_decorator(function_get_language_changer_url)
        def my_view_function(request, somearg):
            pass
    """
    def _decorator(func):
        """
        Decorator function that sets the language changer before calling the wrapped function.

        Args:
            func (function): The function to be wrapped.

        Returns:
            function: The wrapped function.

        Raises:
            None
        """
        def _wrapped(request, *args, **kwargs):
            """
            Wrapper function that sets the language changer and calls the original function.

            Args:
                request (object): The request object.
                *args: Variable length argument list.
                **kwargs: Arbitrary keyword arguments.

            Returns:
                The return value of the original function.
            """
            set_language_changer(request, language_changer)
            return func(request, *args, **kwargs)
        _wrapped.__name__ = func.__name__
        _wrapped.__doc__ = func.__doc__
        return _wrapped
    return _decorator


class DefaultLanguageChanger:
    """
    A class for changing the default language of a web application.

    Attributes:
        request (object): The request object received by the view.
        _app_path (str): The path of the application.

    Methods:
        app_path: Returns the path of the application based on the current language settings.
        get_page_path: Returns the path of the page for a specific language.
        __call__: Changes the language of the web application and returns the corresponding URL.
    """
    def __init__(self, request):
        """
        Initializer for the class.

        Args:
            request: The request object.

        Attributes:
            request: The request object.
            _app_path: The application path.

        Returns:
            None.
        """
        self.request = request
        self._app_path = None

    @property
    def app_path(self):
        """
        Returns the app path based on the current request.

        Returns:
            str: The app path.

        Raises:
            None.

        Note:
            This function is marked as a property and is invoked using the dot notation.
            The app path is determined by first checking the _app_path attribute. If it is None,
            the function calculates the app path based on the current request and other settings.
            If the USE_I18N setting is True, the function tries to get the page path based on the language
            extracted from the current request. Otherwise, it uses the default LANGUAGE_CODE setting.
            If a valid page path is found, the app path is determined by removing the page path from the
            request's path_info attribute. If no page path is found, the app path is same as the request's
            path_info attribute.
        """
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
        """
        Get the path of a page for a specific language.

        Args:
            self (object): The object containing the function.
            lang (str): The language code of the desired language.

        Returns:
            str: The path of the page corresponding to the input language.

        Notes:
            This function relies on the presence of a 'current_page' attribute in the 'request' object.

        Raises:
            None.
        """
        page = getattr(self.request, 'current_page', None)

        if not page:
            return '/%s/' % lang if settings.USE_I18N else '/'

        page_languages = page.get_languages()

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
        """
        Call the function with the given language parameter.

        Args:
            lang (str): The language parameter to be passed to the function.

        Returns:
            str: The URL corresponding to the given language.

        Notes:
            This function is part of a class and is intended to be used as a callable.

        Raises:
            NoReverseMatch: If there is no matching URL for the given language.
            TypeError: If there is a type error when trying to get the absolute URL.
        """
        page_language = get_language_from_request(self.request)
        with force_language(page_language):
            try:
                view = resolve(self.request.path_info)
            except (NoReverseMatch, Resolver404):  # NOQA
                view = None
        if (
            hasattr(self.request, 'toolbar') and
            self.request.toolbar.obj and
            hasattr(self.request.toolbar.obj, "get_absolute_url")
        ):
            # Toolbar object
            if self.request.toolbar.edit_mode_active:
                lang_obj = get_object_for_language(self.request.toolbar.obj, lang, latest=True)
                return '' if lang_obj is None else get_object_edit_url(lang_obj, language=lang)
            if self.request.toolbar.preview_mode_active:
                lang_obj = get_object_for_language(self.request.toolbar.obj, lang, latest=True)
                return '' if lang_obj is None else get_object_preview_url(lang_obj, language=lang)
            try:
                # First see, if object can get language-specific absolute urls (like PageContent)
                return self.request.toolbar.obj.get_absolute_url(language=lang)
            except (TypeError, NoReverseMatch):
                # Object's get_absolute_url does not accept language parameter, set the language
                with force_language(lang):
                    try:
                        url = self.request.toolbar.obj.get_absolute_url()
                    except NoReverseMatch:
                        url = None
                if url:
                    return url
        elif view and view.url_name not in ('pages-details-by-slug', 'pages-root'):
            view_name = view.url_name
            if view.namespace:
                view_name = f"{view.namespace}:{view_name}"
            with force_language(lang):
                try:
                    url = reverse(view_name, args=view.args, kwargs=view.kwargs, current_app=view.app_name)
                except NoReverseMatch:
                    url = None
            if url:
                return url
        return f"{self.get_page_path(lang)}{self.app_path}"

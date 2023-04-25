import functools
import operator
from collections import OrderedDict

from classytags.utils import flatten_context
from django.conf import settings
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, Resolver404, resolve
from django.utils.functional import cached_property
from django.utils.translation import override as force_language

from cms import __version__
from cms.api import get_page_draft
from cms.constants import LEFT, REFRESH_PAGE
from cms.forms.login import CMSToolbarLoginForm
from cms.models import Placeholder, UserSettings
from cms.templates import TemplatesCache
from cms.toolbar.items import ButtonList, Menu, ToolbarAPIMixin
from cms.toolbar_pool import toolbar_pool
from cms.utils import get_language_from_request
from cms.utils.compat import DJANGO_VERSION, PYTHON_VERSION
from cms.utils.compat.dj import installed_apps
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_site_language_from_request


class BaseToolbar(ToolbarAPIMixin):

    watch_models = []
    edit_mode_url_on = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
    edit_mode_url_off = get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
    structure_mode_url_on = get_cms_setting('CMS_TOOLBAR_URL__BUILD')
    disable_url = get_cms_setting('CMS_TOOLBAR_URL__DISABLE')
    color_scheme = get_cms_setting('COLOR_SCHEME')

    @cached_property
    def site_language(self):
        cms_page = get_page_draft(self.request.current_page)
        site_id = cms_page.node.site_id if cms_page else None
        return get_site_language_from_request(self.request, site_id)

    @cached_property
    def request_language(self):
        if settings.USE_I18N:
            language = get_language_from_request(self.request)
        else:
            language = settings.LANGUAGE_CODE
        return language

    def get_content_renderer(self):
        if self.uses_legacy_structure_mode:
            return self.legacy_renderer
        return self.content_renderer

    @cached_property
    def legacy_renderer(self):
        from cms.plugin_rendering import LegacyRenderer

        return LegacyRenderer(request=self.request)

    @cached_property
    def content_renderer(self):
        from cms.plugin_rendering import ContentRenderer

        return ContentRenderer(request=self.request)

    @cached_property
    def structure_renderer(self):
        from cms.plugin_rendering import StructureRenderer

        return StructureRenderer(request=self.request)

    @cached_property
    def structure_mode_active(self):
        structure = get_cms_setting('CMS_TOOLBAR_URL__BUILD')
        return self.is_staff and structure in self.request.GET

    @cached_property
    def edit_mode_active(self):
        if not self.show_toolbar:
            return False
        return self.structure_mode_active or self.content_mode_active

    @cached_property
    def content_mode_active(self):
        if self.structure_mode_active:
            # Structure mode always takes precedence
            return False
        return self.is_staff and self.request.session.get('cms_edit', False)

    @cached_property
    def uses_legacy_structure_mode(self):
        current_page = self.request.current_page

        if not current_page or current_page.application_urls:
            return True
        return False

    @cached_property
    def templates(self):
        return TemplatesCache()


class CMSToolbar(BaseToolbar):
    """
    The default CMS Toolbar
    """

    def __init__(self, request, request_path=None, _async=False):
        super().__init__()
        self._async = _async
        self.right_items = []
        self.left_items = []
        self.last_left_items = []
        self.last_right_items = []
        self.populated = False
        self.post_template_populated = False
        self.menus = {}
        self.obj = None
        self.redirect_url = None
        self.request = None
        self.is_staff = None
        self.show_toolbar = None
        self.clipboard = None
        self.toolbar_language = None
        self.show_toolbar = True
        self.init_toolbar(request, request_path=request_path)
        # Internal attribute to track whether we can cache
        # a response from the current request.
        # This attribute is modified by the placeholder rendering
        # mechanism in case a placeholder rendered by the current
        # request cannot be cached.
        self._cache_disabled = self.edit_mode_active or self.show_toolbar

        with force_language(self.request_language):
            try:
                decorator = resolve(self.request_path).func
                try:
                    # If the original view is decorated we try to extract the real function
                    # module instead of the decorator's one
                    if decorator and getattr(decorator, '__closure__', False):
                        self.app_name = decorator.__closure__[0].cell_contents.__module__
                    else:
                        raise AttributeError()
                except (TypeError, AttributeError):
                    # no decorator
                    self.app_name = decorator.__module__
            except (Resolver404, AttributeError):
                self.app_name = ""
        toolbars = toolbar_pool.get_toolbars()
        parts = self.app_name.split('.')
        while parts:
            path = '.'.join(parts)
            if path in installed_apps():
                self.app_name = path
                break
            parts.pop()

        self.toolbars = OrderedDict()

        for key in toolbars:
            is_current_app = toolbars[key].check_current_app(key, self.app_name)
            toolbar = toolbars[key](
                request=self.request,
                toolbar=self,
                is_current_app=is_current_app,
                app_path=self.app_name,
            )
            self.toolbars[key] = toolbar

    def init_toolbar(self, request, request_path=None):
        self.request = request
        self.is_staff = self.request.user.is_staff
        self.show_toolbar = self.is_staff or self.request.session.get('cms_edit', False)

        if self.request.session.get('cms_toolbar_disabled', False):
            self.show_toolbar = False

        # We need to store the current language in case the user's preferred language is different.
        self.toolbar_language = self.request_language

        if self.is_staff:
            user_settings = self.user_settings
            if (settings.USE_I18N and user_settings.language in dict(settings.LANGUAGES)) or (
                    not settings.USE_I18N and user_settings.language == settings.LANGUAGE_CODE):
                self.toolbar_language = user_settings.language
            else:
                user_settings.language = self.request_language
                user_settings.save()
            self.clipboard = user_settings.clipboard

        if hasattr(self, 'toolbars'):
            for key in self.toolbars:
                self.toolbars[key].request = self.request
        self.request_path = request_path or request.path

    @cached_property
    def user_settings(self):
        return self.get_user_settings()

    @cached_property
    def clipboard_plugin(self):
        if not self.clipboard:
            return None

        try:
            plugin = self.clipboard.get_plugins().select_related('placeholder')[0]
        except IndexError:
            bound_plugin = None
        else:
            bound_plugin = plugin.get_bound_plugin()
        return bound_plugin

    def get_user_settings(self):
        user_settings = None
        if self.is_staff:
            try:
                user_settings = UserSettings.objects.select_related('clipboard').get(user=self.request.user)
            except UserSettings.DoesNotExist:
                placeholder = Placeholder.objects.create(slot="clipboard")
                user_settings = UserSettings.objects.create(
                    clipboard=placeholder,
                    language=self.request_language,
                    user=self.request.user,
                )
        return user_settings

    def _reorder_toolbars(self):
        from cms.cms_toolbars import BasicToolbar
        toolbars = list(self.toolbars.values())
        basic_toolbar = [toolbar for toolbar in toolbars if toolbar.__class__ == BasicToolbar]
        if basic_toolbar and basic_toolbar[0] in toolbars:
            toolbars.remove(basic_toolbar[0])
            toolbars.insert(0, basic_toolbar[0])
        return toolbars

    @property
    def csrf_token(self):
        token = get_token(self.request)
        return token

    # Public API

    def get_menu(self, key, verbose_name=None, side=LEFT, position=None):
        self.populate()
        if key in self.menus:
            return self.menus[key]
        return None

    def get_or_create_menu(self, key, verbose_name=None, disabled=False, side=LEFT, position=None):
        self.populate()
        if key in self.menus:
            menu = self.menus[key]
            if verbose_name:
                menu.name = verbose_name
            if menu.side != side:
                menu.side = side
            if position:
                self.remove_item(menu)
                self.add_item(menu, position=position)
            return menu
        menu = Menu(verbose_name, self.csrf_token, disabled=disabled, side=side)
        self.menus[key] = menu
        self.add_item(menu, position=position)
        return menu

    def add_button(self, name, url, active=False, disabled=False, extra_classes=None, extra_wrapper_classes=None,
                   side=LEFT, position=None):
        self.populate()
        item = ButtonList(extra_classes=extra_wrapper_classes, side=side)
        item.add_button(name, url, active=active, disabled=disabled, extra_classes=extra_classes)
        self.add_item(item, position=position)
        return item

    def add_modal_button(self, name, url, active=False, disabled=False, extra_classes=None, extra_wrapper_classes=None,
                   side=LEFT, position=None, on_close=REFRESH_PAGE):
        self.populate()
        item = ButtonList(extra_classes=extra_wrapper_classes, side=side)
        item.add_modal_button(name, url, active=active, disabled=disabled, extra_classes=extra_classes, on_close=on_close)
        self.add_item(item, position=position)
        return item

    def add_sideframe_button(self, name, url, active=False, disabled=False, extra_classes=None, extra_wrapper_classes=None,
                   side=LEFT, position=None, on_close=None):
        self.populate()
        item = ButtonList(extra_classes=extra_wrapper_classes, side=side)
        item.add_sideframe_button(name, url, active=active, disabled=disabled, extra_classes=extra_classes, on_close=on_close)
        self.add_item(item, position=position)
        return item

    def add_button_list(self, identifier=None, extra_classes=None, side=LEFT, position=None):
        self.populate()
        item = ButtonList(identifier, extra_classes=extra_classes, side=side)
        self.add_item(item, position=position)
        return item

    def set_object(self, obj):
        if not self.obj:
            self.obj = obj

    def get_object_model(self):
        if self.obj:
            return "{0}.{1}".format(self.obj._meta.app_label, self.obj._meta.object_name).lower()
        return ''

    def get_object_pk(self):
        if self.obj:
            return self.obj.pk
        return ''

    def get_object_public_url(self):
        if self.obj:
            with force_language(self.request_language):
                try:
                    return self.obj.get_public_url()
                except:  # noqa: E722
                    pass
        return ''

    def get_object_draft_url(self):
        if self.obj:
            with force_language(self.request_language):
                try:
                    return self.obj.get_draft_url()
                except (NoReverseMatch, AttributeError):
                    try:
                        return self.obj.get_absolute_url()
                    except (NoReverseMatch, AttributeError):
                        pass
        return ''

    # Internal API

    def _add_item(self, item, position=None):
        item.toolbar = self

        if item.right:
            if position and position < 0:
                target = self.last_right_items
                position = abs(position)
            else:
                target = self.right_items
        else:
            if position and position < 0:
                target = self.last_left_items
                position = abs(position)
            else:
                target = self.left_items
        if position is not None:
            target.insert(position, item)
        else:
            target.append(item)

    def _remove_item(self, item):
        if item in self.right_items:
            self.right_items.remove(item)
        elif item in self.last_right_items:
            self.last_right_items.remove(item)
        elif item in self.left_items:
            self.left_items.remove(item)
        elif item in self.last_left_items:
            self.last_left_items.remove(item)
        else:
            raise KeyError("Item %r not found" % item)

    def _item_position(self, item):
        if item.right:
            return self.right_items.index(item)
        else:
            return self.left_items.index(item)

    def get_left_items(self):
        self.populate()
        items = self.left_items + list(reversed(self.last_left_items))
        return items

    def get_right_items(self):
        self.populate()
        items = self.right_items + list(reversed(self.last_right_items))
        return items

    @cached_property
    def media(self):
        self.populate()
        toolbars = self.toolbars.values()
        return functools.reduce(operator.add, (toolbar.media for toolbar in toolbars))

    def populate(self):
        """
        Get the CMS items on the toolbar
        """
        if self.populated:
            return
        self.populated = True
        # never populate the toolbar on is_staff=False
        # FIXME: In 3.1 we should really update the request/staff status
        # when toolbar is used in the cms_toolbar templatetag
        if not self.request.user.is_staff:
            return
        if self.request.session.get('cms_log_latest', False):
            del self.request.session['cms_log_latest']
        self._call_toolbar('populate')

    def post_template_populate(self):
        self.populate()
        if self.post_template_populated:
            return
        self.post_template_populated = True
        # FIXME: In 3.1 we should really update the request/staff status
        # when toolbar is used in the cms_toolbar templatetag
        if not self.request.user.is_staff:
            return
        self._call_toolbar('post_template_populate')

    def _call_toolbar(self, func_name):
        with force_language(self.toolbar_language):
            first = ('cms.cms_toolbars.BasicToolbar', 'cms.cms_toolbars.PlaceholderToolbar')

            for key in first:
                toolbar = self.toolbars.get(key)
                if not toolbar:
                    continue
                getattr(toolbar, func_name)()

            for key in self.toolbars:
                if key in first:
                    continue
                toolbar = self.toolbars[key]
                getattr(toolbar, func_name)()

    def get_render_context(self):
        if self.structure_mode_active and not self.uses_legacy_structure_mode:
            # User has explicitly requested structure mode
            # and the object (page, blog, etc..) allows for the non-legacy structure mode
            renderer = self.structure_renderer
        else:
            renderer = self.get_content_renderer()

        context = {
            'cms_toolbar': self,
            'cms_renderer': renderer,
            'cms_edit_on': self.edit_mode_url_on,
            'cms_edit_off': self.edit_mode_url_off,
            'cms_structure_on': self.structure_mode_url_on,
            'cms_version': __version__,
            'django_version': DJANGO_VERSION,
            'login_form': CMSToolbarLoginForm(),
            'python_version': PYTHON_VERSION,
            'cms_color_scheme': self.color_scheme,
        }
        return context

    def render(self):
        self.populate()
        self.post_template_populate()

        context = self.get_render_context()

        with force_language(self.toolbar_language):
            return render_to_string('cms/toolbar/toolbar.html', context, request=self.request)

    def render_with_structure(self, context, nodelist):
        self.populate()

        context.update(self.get_render_context())

        with force_language(self.toolbar_language):
            # needed to populate the context with sekizai content
            if 'debug' not in context:
                context['debug'] = settings.DEBUG
            render_to_string('cms/toolbar/toolbar_javascript.html', flatten_context(context))

        # render everything below the tag
        rendered_contents = nodelist.render(context)

        self.post_template_populate()

        with force_language(self.toolbar_language):
            # render the toolbar content
            toolbar = render_to_string('cms/toolbar/toolbar_with_structure.html', flatten_context(context))
        # return the toolbar content and the content below
        return '%s\n%s' % (toolbar, rendered_contents)


class EmptyToolbar(BaseToolbar):
    is_staff = False
    show_toolbar = False

    # Backwards compatibility
    edit_mode = False

    _cache_disabled = True

    def __init__(self, request):
        self.request = request
        super().__init__()

# -*- coding: utf-8 -*-
from collections import OrderedDict

from cms.constants import LEFT, REFRESH_PAGE
from cms.models import UserSettings, Placeholder
from cms.toolbar.items import Menu, ToolbarAPIMixin, ButtonList
from cms.toolbar_pool import toolbar_pool
from cms.utils import get_language_from_request
from cms.utils.compat.dj import installed_apps
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import force_language

from django import forms
from django.conf import settings
from django.contrib.auth import login, logout, REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import resolve, Resolver404
from django.http import HttpResponseRedirect, HttpResponse
from django.middleware.csrf import get_token
from django.template import Template
from django.template.loader import get_template
from django.utils.functional import cached_property


class CMSToolbarLoginForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(CMSToolbarLoginForm, self).__init__(*args, **kwargs)
        kwargs['prefix'] = kwargs.get('prefix', 'cms')
        self.fields['username'].widget = forms.TextInput(
            attrs = { 'required': 'required' })
        self.fields['password'].widget = forms.PasswordInput(
            attrs = { 'required': 'required' })


class CMSToolbar(ToolbarAPIMixin):
    """
    The default CMS Toolbar
    """
    watch_models = []

    def __init__(self, request):
        super(CMSToolbar, self).__init__()
        self._cached_templates = {}
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
        self.edit_mode = None
        self.edit_mode_url_on = get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')
        self.edit_mode_url_off = get_cms_setting('CMS_TOOLBAR_URL__EDIT_OFF')
        self.disable_url = get_cms_setting('CMS_TOOLBAR_URL__DISABLE')
        self.build_mode = None
        self.use_draft = None
        self.show_toolbar = None
        self.login_form = None
        self.clipboard = None
        self.language = None
        self.toolbar_language = None
        self.show_toolbar = True
        self.init_toolbar(request)

        with force_language(self.language):
            try:
                decorator = resolve(self.request.path_info).func
                try:
                    # If the original view is decorated we try to extract the real function
                    # module instead of the decorator's one
                    if decorator and getattr(decorator, 'func_closure', False):
                        # python 2
                        self.app_name = decorator.func_closure[0].cell_contents.__module__
                    elif decorator and getattr(decorator, '__closure__', False):
                        # python 3
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
            toolbar = toolbars[key](self.request, self, toolbars[key].check_current_app(key, self.app_name), self.app_name)
            self.toolbars[key] = toolbar

    def init_toolbar(self, request):
        self.request = request
        self.is_staff = self.request.user.is_staff
        self.edit_mode = self.is_staff and self.request.session.get('cms_edit', False)
        self.build_mode = self.is_staff and self.request.session.get('cms_build', False)
        self.use_draft = self.is_staff and self.edit_mode or self.build_mode
        self.show_toolbar = self.is_staff or self.request.session.get('cms_edit', False)
        self.login_form = CMSToolbarLoginForm(request=request)
        if self.request.session.get('cms_toolbar_disabled', False):
            self.show_toolbar = False
        if settings.USE_I18N:
            self.language = get_language_from_request(request)
        else:
            self.language = settings.LANGUAGE_CODE

        # We need to store the current language in case the user's preferred language is different.
        self.toolbar_language = self.language

        user_settings = self.get_user_settings()
        if user_settings:
            if (settings.USE_I18N and user_settings.language in dict(settings.LANGUAGES)) or (
                    not settings.USE_I18N and user_settings.language == settings.LANGUAGE_CODE):
                self.toolbar_language = user_settings.language
            else:
                user_settings.language = self.language
                user_settings.save()
            self.clipboard = user_settings.clipboard

        if hasattr(self, 'toolbars'):
            for key, toolbar in self.toolbars.items():
                self.toolbars[key].request = self.request

    def get_user_settings(self):
        user_settings = None
        if self.is_staff:
            try:
                user_settings = UserSettings.objects.select_related('clipboard').get(user=self.request.user)
            except UserSettings.DoesNotExist:
                placeholder = Placeholder.objects.create(slot="clipboard")
                user_settings = UserSettings.objects.create(
                    clipboard=placeholder,
                    language=self.language,
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

    def render_addons(self, context):
        addons = []
        sorted_toolbars = self._reorder_toolbars()
        for toolbar in sorted_toolbars:
            addons.extend(toolbar.render_addons(context))
        return ''.join(addons)

    def post_template_render_addons(self, context):
        addons = []
        sorted_toolbars = self._reorder_toolbars()
        for toolbar in sorted_toolbars:
            addons.extend(toolbar.post_template_render_addons(context))
        return ''.join(addons)

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
            with force_language(self.language):
                try:
                    return self.obj.get_public_url()
                except:
                    pass
        return ''

    def get_object_draft_url(self):
        if self.obj:
            with force_language(self.language):
                try:
                    return self.obj.get_draft_url()
                except:
                    try:
                        return self.obj.get_absolute_url()
                    except:
                        pass
        return ''

    # Internal API

    def _add_item(self, item, position=None):
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

    def request_hook(self):
        response = self._call_toolbar('request_hook')
        if isinstance(response, HttpResponse):
            return response

        if self.request.method != 'POST':
            return self._request_hook_get()
        else:
            return self._request_hook_post()

    def get_cached_template(self, template):
        if isinstance(template, Template):
            return template

        if not template in self._cached_templates:
            self._cached_templates[template] = get_template(template)
        return self._cached_templates[template]

    @cached_property
    def drag_item_template(self):
        return self.get_cached_template('cms/toolbar/dragitem.html')

    @cached_property
    def drag_item_menu_template(self):
        return self.get_cached_template('cms/toolbar/dragitem_menu.html')

    @cached_property
    def dragbar_template(self):
        return self.get_cached_template('cms/toolbar/dragbar.html')

    def _request_hook_get(self):
        if 'cms-toolbar-logout' in self.request.GET:
            logout(self.request)
            return HttpResponseRedirect(self.request.path_info)

    def _request_hook_post(self):
        # login hook
        if 'cms-toolbar-login' in self.request.GET:
            self.login_form = CMSToolbarLoginForm(request=self.request, data=self.request.POST)
            if self.login_form.is_valid():
                login(self.request, self.login_form.user_cache)
                if REDIRECT_FIELD_NAME in self.request.GET:
                    return HttpResponseRedirect(self.request.GET[REDIRECT_FIELD_NAME])
                else:
                    return HttpResponseRedirect(self.request.path_info)
            else:
                if REDIRECT_FIELD_NAME in self.request.GET:
                    return HttpResponseRedirect(self.request.GET[REDIRECT_FIELD_NAME]+"?cms-toolbar-login-error=1")

    def _call_toolbar(self, func_name):
        with force_language(self.toolbar_language):
            first = ('cms.cms_toolbars.BasicToolbar', 'cms.cms_toolbars.PlaceholderToolbar')
            for key in first:
                toolbar = self.toolbars.get(key)
                if not toolbar:
                    continue
                result = getattr(toolbar, func_name)()
                if isinstance(result, HttpResponse):
                    return result
            for key in self.toolbars:
                if key in first:
                    continue
                toolbar = self.toolbars[key]
                result = getattr(toolbar, func_name)()
                if isinstance(result, HttpResponse):
                    return result

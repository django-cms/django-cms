"""The CMS chrome: the menus the toolbar owns, whatever else is installed.

The site menu, the language menu, the help menu and the appearance switch belong
to the toolbar container, not to any content container. Other containers add
items to these menus by identifier (``ADMIN_MENU_IDENTIFIER`` and friends below),
never by reaching into these classes.

Moved here from ``cms.cms_toolbars``, which stays as the app's toolbar
autodiscovery entry point and re-exports everything.
"""

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_permission_codename, get_user_model
from django.contrib.sites.models import Site
from django.urls import NoReverseMatch
from django.utils.translation import gettext_lazy as _

from cms.shared import resolvers
from cms.toolbar.base import CMSToolbar
from cms.toolbar.items import SubMenu, TemplateItem
from cms.toolbar.pool import toolbar_pool
from cms.utils.conf import get_cms_setting
from cms.utils.i18n import get_language_tuple
from cms.utils.urlutils import admin_reverse
from menus.utils import DefaultLanguageChanger

ADMIN_MENU_IDENTIFIER = "admin-menu"
"""
The *Site* menu (that usually shows the project's domain name, *example.com* by default).
``ADMIN_MENU_IDENTIFIER`` allows you to get hold of this object easily using
:meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
LANGUAGE_MENU_IDENTIFIER = "language-menu"
"""
The *Language* menu. ``LANGUAGE_MENU_IDENTIFIER`` allows you to get hold of this object
easily using :meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
HELP_MENU_IDENTIFIER = "help-menu"
"""
The *Help* menu. ``HELP_MENU_IDENTIFIER`` allows you to get hold of this object easily
using :meth:`cms.toolbar.toolbar.CMSToolbar.get_menu`.
"""
HELP_MENU_BREAK = "Help Menu Break"
ADMIN_SITES_BREAK = "Admin Sites Break"
ADMINISTRATION_BREAK = "Administration Break"
CLIPBOARD_BREAK = "Clipboard Break"
USER_SETTINGS_BREAK = "User Settings Break"
TOOLBAR_DISABLE_BREAK = "Toolbar disable Break"
SHORTCUTS_BREAK = "Shortcuts Break"

DEFAULT_HELP_MENU_ITEMS = (
    (_("Documentation"), "https://docs.django-cms.org/en/stable/"),
    (_("User guide"), "https://user-guide.django-cms.org"),
    (_("Discord community"), "https://www.django-cms.org/discord"),
    (_("What's new"), "https://www.django-cms.org/en/blog/"),
)


@toolbar_pool.register
class AppearanceToolbar(CMSToolbar):
    """
    Adds appearance switches, esp. for dark and light mode
    """

    color_scheme_toggle = get_cms_setting("COLOR_SCHEME_TOGGLE")

    def populate(self):
        if self.color_scheme_toggle:
            dark_mode_toggle = TemplateItem(
                template="cms/toolbar/items/dark_mode_toggle.html",
                side=self.toolbar.RIGHT,
            )
            self.toolbar.add_item(dark_mode_toggle)


@toolbar_pool.register
class HelpToolbar(CMSToolbar):
    """
    Adds a help menu to the toolbar
    """

    def populate(self):
        if not get_cms_setting("ENABLE_HELP"):
            return
        help_menu = self._get_or_create_help_menu()
        self._add_default_menu_items(help_menu)
        self._add_extra_menu_items(help_menu)

    def _get_or_create_help_menu(self) -> SubMenu:
        help_menu = self.toolbar.get_or_create_menu(HELP_MENU_IDENTIFIER, _("Help"), position=-1)
        help_menu.items = []  # reset the items so we don't duplicate
        return help_menu

    def _add_default_menu_items(self, help_menu: SubMenu):
        for label, url in DEFAULT_HELP_MENU_ITEMS:
            help_menu.add_link_item(label, url=url)

    def _add_extra_menu_items(self, help_menu: SubMenu):
        if extra_menu_items := get_cms_setting("EXTRA_HELP_MENU_ITEMS"):
            help_menu.add_break(HELP_MENU_BREAK)
            for label, url in extra_menu_items:
                help_menu.add_link_item(label, url=url)


@toolbar_pool.register
class BasicToolbar(CMSToolbar):
    """
    Basic Toolbar for site and languages menu
    """

    #: Creates the site and language menus that other toolbars add items to,
    #: so it has to populate before them.
    priority = -100

    page = None
    _language_menu = None
    _admin_menu = None

    def init_from_request(self):
        self.page = self.request.current_page

    def populate(self):
        if not self.page:
            self.init_from_request()
            self.clipboard = self.request.toolbar.user_settings.clipboard
            self.add_admin_menu()
            self.add_language_menu()

    def add_admin_menu(self):
        if not self._admin_menu:
            self._admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, self.current_site.name)
            # Users button
            self.add_users_button(self._admin_menu)

            # sites menu
            sites_queryset = Site.objects.order_by("name")

            if len(sites_queryset) > 1:
                sites_menu = self._admin_menu.get_or_create_menu("sites", _("Sites"))
                sites_menu.add_sideframe_item(_("Admin Sites"), url=admin_reverse("sites_site_changelist"))
                sites_menu.add_break(ADMIN_SITES_BREAK)
                for site in sites_queryset:
                    sites_menu.add_link_item(
                        site.name, url="//%s" % site.domain, active=site.pk == self.current_site.pk
                    )

            # admin
            self._admin_menu.add_sideframe_item(_("Administration"), url=admin_reverse("index"))
            self._admin_menu.add_break(ADMINISTRATION_BREAK)

            # cms users settings
            self._admin_menu.add_sideframe_item(_("User settings"), url=admin_reverse("cms_usersettings_change"))
            self._admin_menu.add_break(USER_SETTINGS_BREAK)

            # clipboard
            if self.toolbar.edit_mode_active:
                # True if the clipboard exists and there's plugins in it.
                clipboard_is_bound = self.toolbar.clipboard_plugin

                self._admin_menu.add_link_item(
                    _("Clipboard..."),
                    url="#",
                    extra_classes=["cms-clipboard-trigger"],
                    disabled=not clipboard_is_bound,
                )
                self._admin_menu.add_link_item(
                    _("Clear clipboard"),
                    url="#",
                    extra_classes=["cms-clipboard-empty"],
                    disabled=not clipboard_is_bound,
                )
                self._admin_menu.add_break(CLIPBOARD_BREAK)

            # Disable toolbar
            self._admin_menu.add_link_item(
                _("Disable toolbar"), url="?%s" % get_cms_setting("CMS_TOOLBAR_URL__DISABLE")
            )
            self._admin_menu.add_break(TOOLBAR_DISABLE_BREAK)
            self._admin_menu.add_link_item(_("Shortcuts..."), url="#", extra_classes=("cms-show-shortcuts",))
            self._admin_menu.add_break(SHORTCUTS_BREAK)

            # logout
            self.add_logout_button(self._admin_menu)

    def add_users_button(self, parent):
        User = get_user_model()

        if User in admin.site._registry:
            opts = User._meta

            if self.request.user.has_perm("{}.{}".format(opts.app_label, get_permission_codename("change", opts))):
                user_changelist_url = admin_reverse(f"{opts.app_label}_{opts.model_name}_changelist")
                parent.add_sideframe_item(_("Users"), url=user_changelist_url)

    def add_logout_button(self, parent):
        # Whether the current page survives logging out is a pages question;
        # the chrome only needs the yes/no. Without the pages container the
        # answer is "no", and logout leaves for the site root.
        anon_can_access = resolvers.resolve(
            "anonymous_can_view_page",
            page=self.page,
            site=self.current_site,
            default=False,
        )

        on_success = self.toolbar.REFRESH_PAGE if anon_can_access else "/"

        # We'll show "Logout Joe Bloggs" if the name fields in auth.User are completed, else "Logout jbloggs". If
        # anything goes wrong, it'll just be "Logout".

        user_name = self.get_username()
        logout_menu_text = _("Logout %s") % user_name if user_name else _("Logout")

        parent.add_ajax_item(
            logout_menu_text,
            action=admin_reverse("logout"),
            active=True,
            on_success=on_success,
            method="POST",
        )

    def add_language_menu(self):
        if settings.USE_I18N and not self._language_menu:
            languages = get_language_tuple(self.current_site.pk)
            if len(languages) > 1:
                # Menu only meaningful if more than one language is installed
                self._language_menu = self.toolbar.get_or_create_menu(
                    LANGUAGE_MENU_IDENTIFIER, _("Language"), position=-1
                )
                language_changer = getattr(self.request, "_language_changer", DefaultLanguageChanger(self.request))
                for code, name in languages:
                    try:
                        url = language_changer(code)
                    except NoReverseMatch:
                        url = DefaultLanguageChanger(self.request)(code)
                    if url:
                        self._language_menu.add_link_item(name, url=url, active=self.current_lang == code)
            else:
                # We do not have to check every time the toolbar is created
                self._language_menu = True  # Pretend the language menu is already there

    def get_username(self, user=None, default=""):
        user = user or self.request.user
        try:
            name = user.get_full_name()
            if name:
                return name
            else:
                return user.get_username()
        except (AttributeError, NotImplementedError):
            return default


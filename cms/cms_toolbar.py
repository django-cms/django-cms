# -*- coding: utf-8 -*-
<<<<<<< HEAD
import urllib
from cms import compat
=======
>>>>>>> upstream/develop
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.exceptions import LanguageError
from cms.utils.i18n import get_language_objects, get_language_object
from django.contrib.sites.models import Site
from cms.utils import get_language_from_request, get_cms_setting
from cms.utils.compat.urls import urlencode
from cms.toolbar_pool import toolbar_pool
from cms.utils.permissions import get_user_sites_queryset, has_page_change_permission
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from menus.utils import DefaultLanguageChanger


# Identifiers for search
ADMIN_MENU_IDENTIFIER = 'admin-menu'
TEMPLATE_MENU_BREAK = 'Template Menu Break'
PAGE_MENU_FIRST_BREAK = 'Page Menu First Break'
PAGE_MENU_SECOND_BREAK = 'Page Menu Second Break'
PAGE_MENU_THIRD_BREAK = 'Page Menu Third Break'
HISTORY_MENU_BREAK = 'History Menu Break'
MANAGE_PAGES_BREAK = 'Manage Pages Break'
ADMIN_SITES_BREAK = 'Admin Sites Break'
ADMINISTRATION_BREAK = 'Administration Break'
USER_SETTINGS_BREAK = 'User Settings Break'


def add_page_menu(toolbar, current_page, permissions_active, request):
    # menu for current page
    not_edit_mode = not toolbar.edit_mode
    current_page_menu = toolbar.get_or_create_menu('page', _('Page'))
    current_page_menu.add_link_item(_('Edit Page'), disabled=toolbar.edit_mode, url='?edit')
    page_info_url = reverse('admin:cms_page_change', args=(current_page.pk,))
    current_page_menu.add_modal_item(_('Page info'), url=page_info_url, disabled=not_edit_mode,
                                     close_on_url=toolbar.URL_CHANGE, on_close=toolbar.REFRESH_PAGE)
    if toolbar.build_mode or toolbar.edit_mode:
        # add templates
        templates_menu = current_page_menu.get_or_create_menu('templates', _('Templates'))
        action = reverse('admin:cms_page_change_template', args=(current_page.pk,))
        for path, name in get_cms_setting('TEMPLATES'):
            active = current_page.template == path
            if path == TEMPLATE_INHERITANCE_MAGIC:
                templates_menu.add_break(TEMPLATE_MENU_BREAK)
            templates_menu.add_ajax_item(name, action=action, data={'template': path}, active=active)

    # navigation toggle
    if current_page.in_navigation:
        nav_title = _("Hide in navigation")
    else:
        nav_title = _("Display in navigation")
    nav_action = reverse('admin:cms_page_change_innavigation', args=(current_page.pk,))
    current_page_menu.add_ajax_item(nav_title, action=nav_action, disabled=not_edit_mode)
    current_page_menu.add_break(PAGE_MENU_FIRST_BREAK)
    # move pages
    current_page_menu.add_modal_item(_('Move page'), url=reverse('admin:cms_page_changelist'),
                                     disabled=not_edit_mode)
    # add child/slibling
    add_url = reverse('admin:cms_page_add')
    child_data = {
        'position': 'last-child',
        'target': current_page.pk,
    }
    child_url = '%s?%s' % (add_url, urlencode(child_data))
    current_page_menu.add_modal_item(_('Add child page'), url=child_url, close_on_url=toolbar.URL_CHANGE,
                                     disabled=not_edit_mode)
    sibling_data = {
        'position': 'last-child',
    }
    if current_page.parent_id:
        sibling_data['target'] = current_page.parent_id
    sibling_url = '%s?%s' % (add_url, urlencode(sibling_data))
    current_page_menu.add_modal_item(_('Add sibling page'), url=sibling_url, close_on_url=toolbar.URL_CHANGE,
                                     disabled=not_edit_mode)
    current_page_menu.add_break(PAGE_MENU_SECOND_BREAK)
    # advanced settings
    advanced_url = reverse('admin:cms_page_advanced', args=(current_page.pk,))
    advanced_disabled = not current_page.has_advanced_settings_permission(request) or not toolbar.edit_mode
    current_page_menu.add_modal_item(_('Advanced settings'), url=advanced_url, close_on_url=toolbar.URL_CHANGE,
                                     disabled=advanced_disabled)
    # permissions
    if permissions_active:
        permissions_url = reverse('admin:cms_page_permissions', args=(current_page.pk,))
        permission_disabled = not toolbar.edit_mode or not current_page.has_change_permissions_permission(request)
        current_page_menu.add_modal_item(_('Permissions'), url=permissions_url, close_on_url=toolbar.URL_CHANGE,
                                         disabled=permission_disabled)
    current_page_menu.add_break(PAGE_MENU_THIRD_BREAK)
    # publisher
    if current_page.published:
        publish_title = _('Unpublish page')
    else:
        publish_title = _('Publish page')
    publish_url = reverse('admin:cms_page_change_status', args=(current_page.pk,))
    current_page_menu.add_ajax_item(publish_title, action=publish_url, disabled=not_edit_mode)
    # delete
    delete_url = reverse('admin:cms_page_delete', args=(current_page.pk,))
    current_page_menu.add_modal_item(_('Delete page'), url=delete_url, close_on_url=toolbar.URL_CHANGE,
                                     on_close='/', disabled=not_edit_mode)


def add_history_menu(toolbar, current_page):
    # history menu
    history_menu = toolbar.get_or_create_menu('history', _('History'))
    if 'reversion' in settings.INSTALLED_APPS:
        import reversion
        from reversion.models import Revision

        versions = reversion.get_for_object(current_page)
        if current_page.revision_id:
            current_revision = Revision.objects.get(pk=current_page.revision_id)
            has_undo = versions.filter(revision__pk__lt=current_revision.pk).count() > 0
            has_redo = versions.filter(revision__pk__gt=current_revision.pk).count() > 0
        else:
            has_redo = False
            has_undo = versions.count() > 1
        undo_action = reverse('admin:cms_page_undo', args=(current_page.pk,))
        redo_action = reverse('admin:cms_page_redo', args=(current_page.pk,))
        history_menu.add_ajax_item(_('Undo'), action=undo_action, disabled=not has_undo)
        history_menu.add_ajax_item(_('Redo'), action=redo_action, disabled=not has_redo)
        history_menu.add_break(HISTORY_MENU_BREAK)
    revert_action = reverse('admin:cms_page_revert_page', args=(current_page.pk,))
    revert_question = _('Are you sure you want to revert to live?')
    history_menu.add_ajax_item(_('Revert to live'), action=revert_action, question=revert_question,
                               disabled=not current_page.is_dirty())
    history_menu.add_modal_item(_('View history'), url=reverse('admin:cms_page_history', args=(current_page.pk,)))


def add_cms_menus(toolbar, current_page, permissions_active, request):
    # check global permissions if CMS_PERMISSIONS is active
    if permissions_active:
        has_global_current_page_change_permission = has_page_change_permission(request)
    else:
        has_global_current_page_change_permission = False
        # check if user has page edit permission
    if has_global_current_page_change_permission or toolbar.can_change:
        add_page_menu(toolbar, current_page, permissions_active, request)
        if toolbar.edit_mode:
            # history menu
            add_history_menu(toolbar, current_page)
            # publish button
            if current_page.has_publish_permission(request):
                classes = ["cms_btn-action", "cms_btn-publish"]
                if current_page.is_dirty():
                    classes.append("cms_btn-publish-active")
                if current_page.published:
                    title = _("Publish Changes")
                else:
                    title = _("Publish Page now")
                publish_url = reverse('admin:cms_page_publish_page', args=(current_page.pk,))
                toolbar.add_button(title, url=publish_url, extra_classes=classes, side=toolbar.RIGHT,
                                   disabled=not current_page.is_dirty())


@toolbar_pool.register
def cms_toolbar(toolbar, request, is_current_app, current_app_name):
    toolbar.can_change = request.current_page and request.current_page.has_change_permission(request)
    permissions_active = get_cms_setting('PERMISSION')

    # always use draft if we have a page
    if request.current_page:
        if request.current_page.publisher_is_draft:
            current_page = request.current_page
        else:
            current_page = request.current_page.publisher_draft
    else:
        current_page = None

    current_site = Site.objects.get_current()

    # the main admin menu
    admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, _('Site'))
    # cms page admin
    if toolbar.can_change:
        pages_menu = admin_menu.get_or_create_menu('pages', _('Pages'))
        pages_menu.add_sideframe_item(_('Manage pages'), url=reverse("admin:cms_page_changelist"))
        pages_menu.add_break(MANAGE_PAGES_BREAK)
        pages_menu.add_sideframe_item(_('Add new page'), url=reverse("admin:cms_page_add"))
        # users
    if request.user.has_perm('user.change_user'):
        admin_menu.add_sideframe_item(_('Users'), url=reverse("admin:"+settings.AUTH_USER_MODEL.replace('.','_').lower()+"_changelist"))
    if permissions_active:
        sites_queryset = get_user_sites_queryset(request.user)
    else:
        sites_queryset = Site.objects.all()
    if len(sites_queryset) > 1:
        sites_menu = admin_menu.get_or_create_menu('sites', _('Sites'))
        sites_menu.add_sideframe_item(_('Admin Sites'), url=reverse('admin:sites_site_changelist'))
        sites_menu.add_break(ADMIN_SITES_BREAK)
        for site in sites_queryset:
            sites_menu.add_link_item(site.name, url='http://%s' % site.domain, active=site.pk == current_site.pk)
            # admin
    admin_menu.add_sideframe_item(_('Administration'), url=reverse('admin:index'))
    admin_menu.add_break(ADMINISTRATION_BREAK)
    # cms users
    admin_menu.add_sideframe_item(_('User settings'), url=reverse('admin:cms_usersettings_change'))
    admin_menu.add_break(USER_SETTINGS_BREAK)
    # logout
    admin_menu.add_ajax_item(_('Logout'), action=reverse('admin:logout'), active=True)
    # check if we're in the CMS or on an apphook root
    if current_page:
        path = current_page.get_path()
        if settings.APPEND_SLASH:
            path = "%s/" % path
        if request.path.endswith(path):
            add_cms_menus(toolbar, current_page, permissions_active, request)
            # language menu
    try:
        current_lang = get_language_object(get_language_from_request(request), current_site.pk)
    except LanguageError:
        current_lang = None
    language_menu = toolbar.get_or_create_menu('language', _('Language'))
    language_changer = getattr(request, '_language_changer', DefaultLanguageChanger(request))
    for language in get_language_objects(current_site.pk):
        url = language_changer(language['code'])
        language_menu.add_link_item(language['name'], url=url, active=current_lang == language['code'])
        # edit switcher
    if toolbar.edit_mode and toolbar.can_change:
        switcher = toolbar.add_button_list('Mode Switcher', side=toolbar.RIGHT,
                                           extra_classes=['cms_toolbar-item-cms-mode-switcher'])
        switcher.add_button(_("Content"), '?edit', active=not toolbar.build_mode, disabled=toolbar.build_mode)
        switcher.add_button(_("Structure"), '?build', active=toolbar.build_mode, disabled=not toolbar.build_mode)

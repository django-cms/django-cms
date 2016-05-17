# -*- coding: utf-8 -*-
from logging import getLogger
from os.path import join

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import six
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import get_language, ugettext_lazy as _

from cms import constants
from cms.cache.page import set_xframe_cache, get_xframe_cache
from cms.constants import PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_PENDING, PUBLISHER_STATE_DIRTY, TEMPLATE_INHERITANCE_MAGIC
from cms.exceptions import PublicIsUnmodifiable, LanguageError, PublicVersionNeeded
from cms.models.managers import PageManager, PagePermissionsPermissionManager
from cms.models.metaclasses import PageMetaClass
from cms.publisher.errors import PublisherCantPublish
from cms.utils import i18n, page as page_utils
from cms.utils.conf import get_cms_setting
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.helpers import reversion_register
from menus.menu_pool import menu_pool
from treebeard.mp_tree import MP_Node


logger = getLogger(__name__)


@python_2_unicode_compatible
class Page(six.with_metaclass(PageMetaClass, MP_Node)):
    """
    A simple hierarchical page model
    """
    LIMIT_VISIBILITY_IN_MENU_CHOICES = (
        (constants.VISIBILITY_USERS, _('for logged in users only')),
        (constants.VISIBILITY_ANONYMOUS, _('for anonymous users only')),
    )
    TEMPLATE_DEFAULT = TEMPLATE_INHERITANCE_MAGIC if get_cms_setting('TEMPLATE_INHERITANCE') else get_cms_setting('TEMPLATES')[0][0]

    X_FRAME_OPTIONS_INHERIT = constants.X_FRAME_OPTIONS_INHERIT
    X_FRAME_OPTIONS_DENY = constants.X_FRAME_OPTIONS_DENY
    X_FRAME_OPTIONS_SAMEORIGIN = constants.X_FRAME_OPTIONS_SAMEORIGIN
    X_FRAME_OPTIONS_ALLOW = constants.X_FRAME_OPTIONS_ALLOW
    X_FRAME_OPTIONS_CHOICES = (
        (constants.X_FRAME_OPTIONS_INHERIT, _('Inherit from parent page')),
        (constants.X_FRAME_OPTIONS_DENY, _('Deny')),
        (constants.X_FRAME_OPTIONS_SAMEORIGIN, _('Only this website')),
        (constants.X_FRAME_OPTIONS_ALLOW, _('Allow'))
    )

    template_choices = [(x, _(y)) for x, y in get_cms_setting('TEMPLATES')]

    created_by = models.CharField(
        _("created by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    changed_by = models.CharField(
        _("changed by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    changed_date = models.DateTimeField(auto_now=True)

    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_(
        'When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True,
                                                help_text=_('When to expire the page. Leave empty to never expire.'),
                                                db_index=True)
    #
    # Please use toggle_in_navigation() instead of affecting this property
    # directly so that the cms page cache can be invalidated as appropriate.
    #
    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(_("soft root"), db_index=True, default=False,
                                    help_text=_("All ancestors will not be displayed in the navigation"))
    reverse_id = models.CharField(_("id"), max_length=40, db_index=True, blank=True, null=True, help_text=_(
        "A unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("attached menu"), max_length=80, db_index=True, blank=True, null=True)
    template = models.CharField(_("template"), max_length=100, choices=template_choices,
                                help_text=_('The template used to render the content.'),
                                default=TEMPLATE_DEFAULT)
    site = models.ForeignKey(Site, help_text=_('The site the page is accessible at.'), verbose_name=_("site"),
                             related_name='djangocms_pages')

    login_required = models.BooleanField(_("login required"), default=False)
    limit_visibility_in_menu = models.SmallIntegerField(_("menu visibility"), default=None, null=True, blank=True,
                                                        choices=LIMIT_VISIBILITY_IN_MENU_CHOICES, db_index=True,
                                                        help_text=_("limit when this page is visible in the menu"))
    is_home = models.BooleanField(editable=False, db_index=True, default=False)
    application_urls = models.CharField(_('application'), max_length=200, blank=True, null=True, db_index=True)
    application_namespace = models.CharField(_('application instance name'), max_length=200, blank=True, null=True)

    # Placeholders (plugins)
    placeholders = models.ManyToManyField('cms.Placeholder', editable=False)

    # Publisher fields
    publisher_is_draft = models.BooleanField(default=True, editable=False, db_index=True)
    # This is misnamed - the one-to-one relation is populated on both ends
    publisher_public = models.OneToOneField('self', related_name='publisher_draft', null=True, editable=False)
    languages = models.CharField(max_length=255, editable=False, blank=True, null=True)

    # If the draft is loaded from a reversion version save the revision id here.
    revision_id = models.PositiveIntegerField(default=0, editable=False)

    # X Frame Options for clickjacking protection
    xframe_options = models.IntegerField(
        choices=X_FRAME_OPTIONS_CHOICES,
        default=get_cms_setting('DEFAULT_X_FRAME_OPTIONS'),
    )

    # Managers
    objects = PageManager()
    permissions = PagePermissionsPermissionManager()

    class Meta:
        permissions = (
            ('view_page', 'Can view page'),
            ('publish_page', 'Can publish page'),
            ('edit_static_placeholder', 'Can edit static placeholders'),
        )
        unique_together = (("publisher_is_draft", "site", "application_namespace"),
                           ("reverse_id", "site", "publisher_is_draft"))
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('path',)
        app_label = 'cms'

    def __str__(self):
        try:
            title = self.get_menu_title(fallback=True)
        except LanguageError:
            try:
                title = self.title_set.all()[0]
            except IndexError:
                title = None
        if title is None:
            title = u""
        return force_text(title)

    def __repr__(self):
        # This is needed to solve the infinite recursion when
        # adding new pages.
        return object.__repr__(self)

    @classmethod
    def get_draft_root_node(cls, position=None, site=None):
        """
        Returns the last draft root node if no position is specified.
        If a position is specified, returns the draft root node in the
        given position raising an IndexError if no such position exists.
        """
        # Only look at nodes marked as draft.
        nodes = cls.get_root_nodes().filter(publisher_is_draft=True)

        if site:
            # Filter out any nodes not belonging to provided site.
            nodes = nodes.filter(site=site)

        if position is None:
            # No position has been given.
            # We default to the last root node
            nodes = nodes.reverse()
            position = 0
        return nodes[position]

    def is_dirty(self, language):
        state = self.get_publisher_state(language)
        return state == PUBLISHER_STATE_DIRTY or state == PUBLISHER_STATE_PENDING

    def get_absolute_url(self, language=None, fallback=True):
        if not language:
            language = get_language()
        with i18n.force_language(language):
            if self.is_home:
                return reverse('pages-root')
            path = self.get_path(language, fallback) or self.get_slug(language, fallback)
            return reverse('pages-details-by-slug', kwargs={"slug": path})

    def get_public_url(self, language=None, fallback=True):
        """
        Returns the URL of the published version of the current page.
        Returns empty string if the page is not published.
        """
        try:
            return self.get_public_object().get_absolute_url(language, fallback)
        except:
            return ''

    def get_draft_url(self, language=None, fallback=True):
        """
        Returns the URL of the draft version of the current page.
        Returns empty string if the draft page is not available.
        """
        try:
            return self.get_draft_object().get_absolute_url(language, fallback)
        except:
            return ''

    def move_page(self, target, position='first-child'):
        """
        Called from admin interface when page is moved. Should be used on
        all the places which are changing page position. Used like an interface
        to django-treebeard, but after move is done page_moved signal is fired.

        Note for issue #1166: url conflicts are handled by updated
        check_title_slugs, overwrite_url on the moved page don't need any check
        as it remains the same regardless of the page position in the tree
        """
        assert self.publisher_is_draft
        assert target.publisher_is_draft
        # do not mark the page as dirty after page moves
        self._publisher_keep_state = True

        is_inherited_template = (
            self.template == constants.TEMPLATE_INHERITANCE_MAGIC)
        target_public_page = None

        if position in ('left', 'right') and not target.parent:
            # make sure move_page does not break the tree
            # when moving to a top level position.

            if position == 'right' and target.publisher_public_id:
                # The correct path order for pages at the root level
                # is that any left sibling page has a path
                # lower than the path of the current page.
                # This rule applies to both draft and live pages
                # so this condition will make sure to add the
                # current page to the right of the target live page.
                target_public_page = Page.objects.get(pk=target.publisher_public_id)
                draft_root = target.get_root()
                public_root = target_public_page.get_root()

                # With this assert we can detect tree corruptions.
                # It's important to raise this!
                assert draft_root.get_next_sibling() == public_root

            if is_inherited_template:
                # The following code resolves the inherited template
                # and sets it on the moved page.
                # This is because the page is being moved to a root
                # position and so can't inherit from anything.
                self.template = self.get_template()

        if position == 'first-child' or position == 'last-child':
            self.parent_id = target.pk
        else:
            self.parent_id = target.parent_id

        self.save()

        if target_public_page:
            moved_page = self.move(target_public_page, pos=position)
        else:
            moved_page = self.move(target, pos=position)

        # fire signal
        import cms.signals as cms_signals
        cms_signals.page_moved.send(sender=Page, instance=moved_page)

        # check the slugs
        page_utils.check_title_slugs(moved_page)

        # Make sure to update the slug and path of the target page.
        page_utils.check_title_slugs(target)

        if target_public_page:
             page_utils.check_title_slugs(target)

        if moved_page.publisher_public_id:
            # Ensure we have up to date mptt properties
            public_page = Page.objects.get(pk=moved_page.publisher_public_id)
            # Ensure that the page is in the right position and save it
            public_page = moved_page._publisher_save_public(public_page)
            cms_signals.page_moved.send(sender=Page, instance=public_page)

            page_utils.check_title_slugs(public_page)

        # Update the descendants to "PENDING"
        # If the target (parent) page is not published
        # and the page being moved is published.
        titles = (
            moved_page
            .title_set
            .filter(language__in=moved_page.get_languages())
            .values_list('language', 'published')
        )

        if moved_page.parent_id:
            parent_titles = (
                moved_page
                .parent
                .title_set
                .values_list('language', 'published')
            )
            parent_titles_by_language = dict(parent_titles)
        else:
            parent_titles_by_language = {}

        for language, published in titles:
            if moved_page.parent_id:
                parent_is_published = parent_titles_by_language.get(language)

                if parent_is_published and published:
                    # this looks redundant but it's necessary
                    # for all the descendants of the page being
                    # copied to be set to the correct state.
                    moved_page.mark_as_published(language)
                    moved_page.mark_descendants_as_published(language)
                elif published:
                    # page is published but it's parent is not
                    # mark the page being copied (source) as "pending"
                    moved_page.mark_as_pending(language)
                    # mark all descendants of source as "pending"
                    moved_page.mark_descendants_pending(language)
            elif published:
                moved_page.mark_as_published(language)
                moved_page.mark_descendants_as_published(language)

        from cms.cache import invalidate_cms_page_cache
        invalidate_cms_page_cache()

    def _copy_titles(self, target, language, published):
        """
        Copy all the titles to a new page (which must have a pk).
        :param target: The page where the new titles should be stored
        """
        from .titlemodels import Title

        old_titles = dict(target.title_set.filter(language=language).values_list('language', 'pk'))
        for title in self.title_set.filter(language=language):
            old_pk = title.pk
            # If an old title exists, overwrite. Otherwise create new
            title.pk = old_titles.pop(title.language, None)
            title.page = target
            title.publisher_is_draft = target.publisher_is_draft
            title.publisher_public_id = old_pk
            if published:
                title.publisher_state = PUBLISHER_STATE_DEFAULT
            else:
                title.publisher_state = PUBLISHER_STATE_PENDING
            title.published = published
            title._publisher_keep_state = True
            title.save()

            old_title = Title.objects.get(pk=old_pk)
            old_title.publisher_public = title
            old_title.publisher_state = title.publisher_state
            old_title.published = True
            old_title._publisher_keep_state = True
            old_title.save()
            if hasattr(self, 'title_cache'):
                self.title_cache[language] = old_title
        if old_titles:
            Title.objects.filter(id__in=old_titles.values()).delete()

    def _copy_contents(self, target, language):
        """
        Copy all the plugins to a new page.
        :param target: The page where the new content should be stored
        """
        # TODO: Make this into a "graceful" copy instead of deleting and overwriting
        # copy the placeholders (and plugins on those placeholders!)
        from cms.models.pluginmodel import CMSPlugin
        from cms.plugin_pool import plugin_pool

        plugin_pool.set_plugin_meta()
        for plugin in CMSPlugin.objects.filter(placeholder__page=target, language=language).order_by('-depth'):
            inst, cls = plugin.get_plugin_instance()
            if inst and getattr(inst, 'cmsplugin_ptr_id', False):
                inst.cmsplugin_ptr = plugin
                inst.cmsplugin_ptr._no_reorder = True
                inst.delete(no_mp=True)
            else:
                plugin._no_reorder = True
                plugin.delete(no_mp=True)
        new_phs = []
        target_phs = target.placeholders.all()
        for ph in self.get_placeholders():
            plugins = ph.get_plugins_list(language)
            found = False
            for target_ph in target_phs:
                if target_ph.slot == ph.slot:
                    ph = target_ph
                    found = True
                    break
            if not found:
                ph.pk = None  # make a new instance
                ph.save()
                new_phs.append(ph)
                # update the page copy
            if plugins:
                copy_plugins_to(plugins, ph)
        target.placeholders.add(*new_phs)

    def _copy_attributes(self, target, clean=False):
        """
        Copy all page data to the target. This excludes parent and other values
        that are specific to an exact instance.
        :param target: The Page to copy the attributes to
        """
        if not clean:
            target.publication_date = self.publication_date
            target.publication_end_date = self.publication_end_date
            target.reverse_id = self.reverse_id
        target.login_required = self.login_required
        target.in_navigation = self.in_navigation
        target.soft_root = self.soft_root
        target.limit_visibility_in_menu = self.limit_visibility_in_menu
        target.navigation_extenders = self.navigation_extenders
        target.application_urls = self.application_urls
        target.application_namespace = self.application_namespace
        target.template = self.template
        target.site_id = self.site_id
        target.xframe_options = self.xframe_options

    def copy_page(self, target, site, position='first-child',
                  copy_permissions=True):
        """
        Copy a page [ and all its descendants to a new location ]
        Doesn't checks for add page permissions anymore, this is done in PageAdmin.

        Note for issue #1166: when copying pages there is no need to check for
        conflicting URLs as pages are copied unpublished.
        """
        from cms.extensions import extension_pool
        from cms.models import Placeholder

        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable("copy page is not allowed for public pages")
        pages = list(self.get_descendants(True).order_by('path'))
        site_reverse_ids = Page.objects.filter(site=site, reverse_id__isnull=False).values_list('reverse_id', flat=True)
        if target:
            target.old_pk = -1
            if position == "first-child" or position == "last-child":
                tree = [target]
            elif target.parent_id:
                tree = [target.parent]
            else:
                tree = []
        else:
            tree = []
        if tree:
            tree[0].old_pk = tree[0].pk
        first = True
        first_page = None
        # loop over all affected pages (self is included in descendants)
        for page in pages:
            titles = list(page.title_set.all())
            # get all current placeholders (->plugins)
            placeholders = list(page.get_placeholders())
            origin_id = page.id
            # create a copy of this page by setting pk = None (=new instance)
            page.old_pk = old_pk = page.pk
            page.pk = None
            page.path = None
            page.depth = None
            page.numchild = 0
            page.publisher_public_id = None
            page.is_home = False
            page.site = site
            # only set reverse_id on standard copy
            if page.reverse_id in site_reverse_ids:
                page.reverse_id = None
            if first:
                first = False
                if tree:
                    page.parent = tree[0]
                else:
                    page.parent = None
                page.save()
                first_page = page
                if target:
                    page = page.move(target, pos=position)
                    page.old_pk = old_pk
            else:
                count = 1
                found = False
                for prnt in tree:
                    if tree[0].pk == self.pk and page.parent_id == self.pk and count == 1:
                        count += 1
                        continue
                    elif prnt.old_pk == page.parent_id:
                        page.parent_id = prnt.pk
                        tree = tree[0:count]
                        found = True
                        break
                    count += 1
                if not found:
                    page.parent = None
                    page.parent_id = None
                page.save()
            tree.append(page)

            # copy permissions if necessary
            if get_cms_setting('PERMISSION') and copy_permissions:
                from cms.models.permissionmodels import PagePermission

                for permission in PagePermission.objects.filter(page__id=origin_id):
                    permission.pk = None
                    permission.page = page
                    permission.save()

            # copy titles of this page
            draft_titles = {}
            for title in titles:

                title.pk = None  # setting pk = None creates a new instance
                title.page = page
                if title.publisher_public_id:
                    draft_titles[title.publisher_public_id] = title
                    title.publisher_public = None
                    # create slug-copy for standard copy
                title.published = False
                title.slug = page_utils.get_available_slug(title)
                title.save()
            # copy the placeholders (and plugins on those placeholders!)
            for ph in placeholders:
                plugins = ph.get_plugins_list()
                try:
                    ph = page.placeholders.get(slot=ph.slot)
                except Placeholder.DoesNotExist:
                    ph.pk = None  # make a new instance
                    ph.save()
                    page.placeholders.add(ph)
                if plugins:
                    copy_plugins_to(plugins, ph)
            extension_pool.copy_extensions(Page.objects.get(pk=origin_id), page)
        # invalidate the menu for this site
        menu_pool.clear(site_id=site.pk)
        return first_page

    def delete(self, *args, **kwargs):
        pages = [self.pk]
        if self.publisher_public_id:
            pages.append(self.publisher_public_id)
        self.__class__.objects.filter(pk__in=pages).delete()

    def save(self, no_signals=False, commit=True, **kwargs):
        """
        Args:
            commit: True if model should be really saved
        """
        # delete template cache
        if hasattr(self, '_template_cache'):
            delattr(self, '_template_cache')

        created = not bool(self.pk)
        if self.reverse_id == "":
            self.reverse_id = None
        if self.application_namespace == "":
            self.application_namespace = None
        from cms.utils.permissions import _thread_locals

        user = getattr(_thread_locals, "user", None)
        if user:
            try:
                changed_by = force_text(user)
            except AttributeError:
                # AnonymousUser may not have USERNAME_FIELD
                changed_by = "anonymous"
            else:
                # limit changed_by and created_by to avoid problems with Custom User Model
                if len(changed_by) > constants.PAGE_USERNAME_MAX_LENGTH:
                    changed_by = u'{0}... (id={1})'.format(
                        changed_by[:constants.PAGE_USERNAME_MAX_LENGTH - 15],
                        user.pk,
                    )

            self.changed_by = changed_by

        else:
            self.changed_by = "script"
        if created:
            self.created_by = self.changed_by

        if commit:
            if not self.depth:
                if self.parent_id:
                    self.depth = self.parent.depth + 1
                    self.parent.add_child(instance=self)
                else:
                    self.add_root(instance=self)
                return  #add_root and add_child save as well
            super(Page, self).save(**kwargs)

    def save_base(self, *args, **kwargs):
        """Overridden save_base. If an instance is draft, and was changed, mark
        it as dirty.

        Dirty flag is used for changed nodes identification when publish method
        takes place. After current changes are published, state is set back to
        PUBLISHER_STATE_DEFAULT (in publish method).
        """
        keep_state = getattr(self, '_publisher_keep_state', None)
        if self.publisher_is_draft and not keep_state and self.is_new_dirty():
            self.title_set.all().update(publisher_state=PUBLISHER_STATE_DIRTY)
        if keep_state:
            delattr(self, '_publisher_keep_state')
        return super(Page, self).save_base(*args, **kwargs)

    def is_new_dirty(self):
        if self.pk:
            fields = [
                'publication_date', 'publication_end_date', 'in_navigation', 'soft_root', 'reverse_id',
                'navigation_extenders', 'template', 'login_required', 'limit_visibility_in_menu'
            ]
            try:
                old_page = Page.objects.get(pk=self.pk)
            except Page.DoesNotExist:
                return True
            for field in fields:
                old_val = getattr(old_page, field)
                new_val = getattr(self, field)
                if not old_val == new_val:
                    return True
            return False
        return True

    def is_published(self, language, force_reload=False):
        return self.get_title_obj(language, False, force_reload=force_reload).published

    def toggle_in_navigation(self, set_to=None):
        '''
        Toggles (or sets) in_navigation and invalidates the cms page cache
        '''
        old = self.in_navigation
        if set_to in [True, False]:
            self.in_navigation = set_to
        else:
            self.in_navigation = not self.in_navigation
        self.save()

        #
        # If there was a change, invalidate the cms page cache
        #
        if self.in_navigation != old:
            from cms.cache import invalidate_cms_page_cache
            invalidate_cms_page_cache()

        return self.in_navigation

    def get_publisher_state(self, language, force_reload=False):
        try:
            return self.get_title_obj(language, False, force_reload=force_reload).publisher_state
        except AttributeError:
            return None

    def set_publisher_state(self, language, state, published=None):
        title = self.title_set.get(language=language)
        title.publisher_state = state
        if published is not None:
            title.published = published
        title._publisher_keep_state = True
        title.save()
        if hasattr(self, 'title_cache') and language in self.title_cache:
            self.title_cache[language].publisher_state = state
        return title

    def publish(self, language):
        """Overrides Publisher method, because there may be some descendants, which
        are waiting for parent to publish, so publish them if possible.

        :returns: True if page was successfully published.
        """
        # Publish can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be published. Use draft.')

        # publish, but only if all parents are published!!
        published = None

        if not self.pk:
            self.save()
            # be sure we have the newest data including mptt
        p = Page.objects.get(pk=self.pk)
        self.path = p.path
        self.depth = p.depth
        self.numchild = p.numchild
        if self._publisher_can_publish():
            if self.publisher_public_id:
                # Ensure we have up to date mptt properties
                public_page = Page.objects.get(pk=self.publisher_public_id)
            else:
                public_page = Page(created_by=self.created_by)
            if not self.publication_date:
                self.publication_date = now()
            self._copy_attributes(public_page)
            # we need to set relate this new public copy to its draft page (self)
            public_page.publisher_public = self
            public_page.publisher_is_draft = False

            # Ensure that the page is in the right position and save it
            self._publisher_save_public(public_page)
            public_page = public_page.reload()
            published = public_page.parent_id is None or public_page.parent.is_published(language)
            if not public_page.pk:
                public_page.save()
            # The target page now has a pk, so can be used as a target
            self._copy_titles(public_page, language, published)
            self._copy_contents(public_page, language)
            # trigger home update
            public_page.save()
            # invalidate the menu for this site
            menu_pool.clear(site_id=self.site_id)
            self.publisher_public = public_page
            published = True
        else:
            # Nothing left to do
            pass
        if not published:
            self.set_publisher_state(language, PUBLISHER_STATE_PENDING, published=True)
        self._publisher_keep_state = True
        self.save()
        # If we are publishing, this page might have become a "home" which
        # would change the path
        if self.is_home:
            for title in self.title_set.all():
                if title.path != '':
                    title._publisher_keep_state = True
                    title.save()
        if not published:
            # was not published, escape
            return

        # Check if there are some children which are waiting for parents to
        # become published.
        self.mark_descendants_as_published(language)

        # fire signal after publishing is done
        import cms.signals as cms_signals

        cms_signals.post_publish.send(sender=Page, instance=self, language=language)

        from cms.cache import invalidate_cms_page_cache
        invalidate_cms_page_cache()

        return published

    def unpublish(self, language):
        """
        Removes this page from the public site
        :returns: True if this page was successfully unpublished
        """
        # Publish can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be unpublished. Use draft.')

        # First, make sure we are in the correct state
        title = self.title_set.get(language=language)
        public_title = title.publisher_public
        title.published = False
        title.publisher_state = PUBLISHER_STATE_DIRTY
        title.save()
        if hasattr(self, 'title_cache'):
            self.title_cache[language] = title
        public_title.published = False
        public_title.save()

        public_page = self.publisher_public
        public_placeholders = public_page.get_placeholders()
        for pl in public_placeholders:
            pl.cmsplugin_set.filter(language=language).delete()
        public_page.save()
        # trigger update home
        self.save()
        self.mark_descendants_pending(language)

        from cms.cache import invalidate_cms_page_cache
        invalidate_cms_page_cache()

        from cms.signals import post_unpublish
        post_unpublish.send(sender=Page, instance=self, language=language)

        return True

    def mark_as_pending(self, language):
        public = self.get_public_object()

        if public:
            state = public.get_publisher_state(language)
            # keep the same state
            # only set the page as unpublished
            public.set_publisher_state(
                language,
                state=state,
                published=False
            )

        draft = self.get_draft_object()

        if draft and draft.is_published(language) and draft.get_publisher_state(
                language) == PUBLISHER_STATE_DEFAULT:
            # Only change the state if the draft page is published
            # and it's state is the default (0)
            draft.set_publisher_state(language, state=PUBLISHER_STATE_PENDING)

    def mark_descendants_pending(self, language):
        assert self.publisher_is_draft

        # Go through all children of our public instance
        public_page = self.publisher_public

        if public_page:
            descendants = public_page.get_descendants().filter(title_set__language=language)

            for child in descendants:
                child.mark_as_pending(language)

    def mark_as_published(self, language):
        from cms.models import Title

        public = self.get_public_object()

        if public:
            try:
                public_published = public.is_published(language)
            except Title.DoesNotExist:
                public_published = False

            if public_published:
                public.set_publisher_state(
                    language,
                    state=PUBLISHER_STATE_DEFAULT,
                    published=True
                )

        draft = self.get_draft_object()

        if draft.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
            draft.set_publisher_state(language, PUBLISHER_STATE_DEFAULT)

    def mark_descendants_as_published(self, language):
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be published. Use draft.')

        # Check if there are some children which are waiting for parents to
        # become published.
        from cms.models import Title

        # List of published draft pages
        publish_set = list(
            self.get_descendants()
            .filter(title_set__published=True, title_set__language=language)
            .select_related('publisher_public', 'publisher_public__parent')
            .order_by('depth', 'path')
        )

        # prefetch the titles
        page_ids = []

        for page in publish_set:
            if not page.pk in page_ids:
                page_ids.append(page.pk)

            publisher_id = page.publisher_public_id

            if publisher_id and not publisher_id in page_ids:
                page_ids.append(publisher_id)

        titles = Title.objects.filter(page__pk__in=page_ids, language=language)
        titles_by_page_id = {}

        for title in titles:
            titles_by_page_id[title.page_id] = title

        for page in publish_set:
            if page.pk in titles_by_page_id:
                page.title_cache = {language: titles_by_page_id[page.pk]}

            if page.publisher_public_id:
                # Page has a public version
                publisher_public = page.publisher_public

                if not publisher_public.parent_id:
                    # This page clearly has a parent because it shows up
                    # when calling self.get_descendants()
                    # So this condition can be True when a published page
                    # is moved under a page that has never been published.
                    # It's draft version (page) has a reference to the new parent
                    # but it's live version does not because it was never set
                    # since it didn't exist when the move happened.
                    publisher_public = page._publisher_save_public(publisher_public)

                # Check if the parent of this page's
                # public version is published.
                if publisher_public.parent.is_published(language):
                    public_title = titles_by_page_id.get(page.publisher_public_id)

                    if public_title and not public_title.published:
                        public_title._publisher_keep_state = True
                        public_title.published = True
                        public_title.publisher_state = PUBLISHER_STATE_DEFAULT
                        public_title.save()

                    draft_title = titles_by_page_id[page.pk]

                    if draft_title.publisher_state == PUBLISHER_STATE_PENDING:
                        draft_title.publisher_state = PUBLISHER_STATE_DEFAULT
                        draft_title._publisher_keep_state = True
                        draft_title.save()
            elif page.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
                page.publish(language)

    def revert(self, language):
        """Revert the draft version to the same state as the public version
        """
        # Revert can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be reverted. Use draft.')
        if not self.publisher_public:
            raise PublicVersionNeeded('A public version of this page is needed')
        public = self.publisher_public
        public._copy_titles(self, language, public.is_published(language))
        public._copy_contents(self, language)
        public._copy_attributes(self)
        self.title_set.filter(language=language).update(publisher_state=PUBLISHER_STATE_DEFAULT, published=True)
        self.revision_id = 0
        self._publisher_keep_state = True
        self.save()

    def get_draft_object(self):
        if not self.publisher_is_draft:
            return self.publisher_draft
        return self

    def get_public_object(self):
        if not self.publisher_is_draft:
            return self
        return self.publisher_public

    def get_languages(self):
        if self.languages:
            return sorted(self.languages.split(','))
        else:
            return []

    def get_descendants(self, include_self=False):
        """
        :returns: A queryset of all the node's descendants as DFS, doesn't
            include the node itself
        """
        if include_self:
            return self.__class__.get_tree(self).filter(site_id=self.site_id)
        else:
            return self.__class__.get_tree(self).exclude(pk=self.pk).filter(site_id=self.site_id)

    def get_published_languages(self):
        if self.publisher_is_draft:
            return self.get_languages()
        return sorted([language for language in self.get_languages() if self.is_published(language)])

    def get_cached_ancestors(self):
        # Unlike MPTT, Treebeard returns this in parent->child order, so you will have to reverse
        # this list to have the same behavior as before
        if not hasattr(self, "ancestors_ascending"):
            self.ancestors_ascending = list(self.get_ancestors())
        return self.ancestors_ascending

    def get_cached_descendants(self):
        if not hasattr(self, "_cached_descendants"):
            self._cached_descendants = list(self.get_descendants())
        return self._cached_descendants

    # ## Title object access

    def get_title_obj(self, language=None, fallback=True, version_id=None, force_reload=False):
        """Helper function for accessing wanted / current title.
        If wanted title doesn't exists, EmptyTitle instance will be returned.
        """
        language = self._get_title_cache(language, fallback, version_id, force_reload)
        if language in self.title_cache:
            return self.title_cache[language]
        from cms.models.titlemodels import EmptyTitle

        return EmptyTitle(language)

    def get_title_obj_attribute(self, attrname, language=None, fallback=True, version_id=None, force_reload=False):
        """Helper function for getting attribute or None from wanted/current title.
        """
        try:
            attribute = getattr(self.get_title_obj(
                language, fallback, version_id, force_reload), attrname)
            return attribute
        except AttributeError:
            return None

    def get_path(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the path of the page depending on the given language
        """
        return self.get_title_obj_attribute("path", language, fallback, version_id, force_reload)

    def get_slug(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the slug of the page depending on the given language
        """
        return self.get_title_obj_attribute("slug", language, fallback, version_id, force_reload)

    def get_title(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the title of the page depending on the given language
        """
        return self.get_title_obj_attribute("title", language, fallback, version_id, force_reload)

    def get_menu_title(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the menu title of the page depending on the given language
        """
        menu_title = self.get_title_obj_attribute("menu_title", language, fallback, version_id, force_reload)
        if not menu_title:
            return self.get_title(language, True, version_id, force_reload)
        return menu_title

    def get_placeholders(self):
        if not hasattr(self, '_placeholder_cache'):
            self._placeholder_cache = self.placeholders.all()
        return self._placeholder_cache

    def _validate_title(self, title):
        from cms.models.titlemodels import EmptyTitle
        if isinstance(title, EmptyTitle):
            return False
        if not title.title or not title.slug:
            return False
        return True

    def get_admin_tree_title(self):
        from cms.models.titlemodels import EmptyTitle
        language = get_language()
        if not hasattr(self, 'title_cache'):
            self.title_cache = {}
            for title in self.title_set.all():
                self.title_cache[title.language] = title
        if language not in self.title_cache or not self._validate_title(self.title_cache.get(language, EmptyTitle(language))):
            fallback_langs = i18n.get_fallback_languages(language)
            found = False
            for lang in fallback_langs:
                if lang in self.title_cache and self._validate_title(self.title_cache.get(lang, EmptyTitle(lang))):
                    found = True
                    language = lang
            if not found:
                language = None
                for lang, item in self.title_cache.items():
                    if not isinstance(item, EmptyTitle):
                        language = lang
        if not language:
            return _("Empty")
        title = self.title_cache[language]
        if title.title:
            return title.title
        if title.page_title:
            return title.page_title
        if title.menu_title:
            return title.menu_title
        return title.slug

    def get_changed_date(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get when this page was last updated
        """
        return self.changed_date

    def get_changed_by(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get user who last changed this page
        """
        return self.changed_by

    def get_page_title(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the page title of the page depending on the given language
        """
        page_title = self.get_title_obj_attribute("page_title", language, fallback, version_id, force_reload)
        if not page_title:
            return self.get_title(language, True, version_id, force_reload)
        return page_title

    def get_meta_description(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get content for the description meta tag for the page depending on the given language
        """
        return self.get_title_obj_attribute("meta_description", language, fallback, version_id, force_reload)

    def get_application_urls(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get application urls conf for application hook
        """
        return self.application_urls

    def get_redirect(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get redirect
        """
        return self.get_title_obj_attribute("redirect", language, fallback, version_id, force_reload)

    def _get_title_cache(self, language, fallback, version_id, force_reload):
        if not language:
            language = get_language()
        load = False
        if not hasattr(self, "title_cache") or force_reload:
            load = True
            self.title_cache = {}
        elif language not in self.title_cache:
            if fallback:
                fallback_langs = i18n.get_fallback_languages(language)
                for lang in fallback_langs:
                    if lang in self.title_cache:
                        return lang
            load = True
        if load:
            from cms.models.titlemodels import Title

            if version_id:
                from cms.utils.reversion_hacks import Version

                version = get_object_or_404(Version, pk=version_id)
                revs = [related_version.object_version for related_version in version.revision.version_set.all()]
                for rev in revs:
                    obj = rev.object
                    if obj.__class__ == Title:
                        self.title_cache[obj.language] = obj
            else:
                titles = Title.objects.filter(page=self)
                for title in titles:
                    self.title_cache[title.language] = title
                if language in self.title_cache:
                    return language
                else:
                    if fallback:
                        fallback_langs = i18n.get_fallback_languages(language)
                        for lang in fallback_langs:
                            if lang in self.title_cache:
                                return lang
        return language

    def get_template(self):
        """
        get the template of this page if defined or if closer parent if
        defined or DEFAULT_PAGE_TEMPLATE otherwise
        """
        if hasattr(self, '_template_cache'):
            return self._template_cache
        template = None
        if self.template:
            if self.template != constants.TEMPLATE_INHERITANCE_MAGIC:
                template = self.template
            else:
                try:
                    template = list(
                        reversed(
                            self.get_ancestors().exclude(
                                template=constants.TEMPLATE_INHERITANCE_MAGIC
                            ).values_list('template', flat=True)
                        )
                    )[0]
                except IndexError:
                    pass
        if not template:
            template = get_cms_setting('TEMPLATES')[0][0]
        self._template_cache = template
        return template

    def get_template_name(self):
        """
        get the textual name (2nd parameter in get_cms_setting('TEMPLATES'))
        of the template of this page or of the nearest
        ancestor. failing to find that, return the name of the default template.
        """
        template = self.get_template()
        for t in get_cms_setting('TEMPLATES'):
            if t[0] == template:
                return t[1]
        return _("default")

    def has_view_permission(self, request, user=None):
        if not user:
            user = request.user
        from cms.utils.permissions import get_any_page_view_permissions, has_global_page_permission
        can_see_unrestricted = get_cms_setting('PUBLIC_FOR') == 'all' or (
            get_cms_setting('PUBLIC_FOR') == 'staff' and user.is_staff)

        # inherited and direct view permissions
        is_restricted = bool(get_any_page_view_permissions(request, self))

        if not is_restricted and can_see_unrestricted:
            return True
        elif not user.is_authenticated():
            return False

        if not is_restricted:
            # a global permission was given to the request's user
            if has_global_page_permission(request, self.site_id, user=user, can_view=True):
                return True
        else:
            # a specific permission was granted to the request's user
            if self.get_draft_object().has_generic_permission(request, "view", user=user):
                return True

        # The user has a normal django permission to view pages globally
        opts = self._meta
        codename = '%s.view_%s' % (opts.app_label, opts.object_name.lower())
        return request.user.has_perm(codename)

    def has_change_permission(self, request, user=None):
        from cms.utils.permissions import has_auth_page_permission

        if not user:
            user = request.user

        if user.is_superuser:
            return True
        return (has_auth_page_permission(user, action='change')
                and self.has_generic_permission(request, "change"))

    def has_delete_permission(self, request, user=None):
        from cms.utils.permissions import has_auth_page_permission

        if not user:
            user = request.user

        if user.is_superuser:
            return True
        return (has_auth_page_permission(user, action='delete')
                and self.has_generic_permission(request, "delete"))

    def has_publish_permission(self, request, user=None):
        if not user:
            user = request.user
        if user.is_superuser:
            return True
        opts = self._meta
        return (user.has_perm(opts.app_label + '.' + "publish_page")
                and self.has_generic_permission(request, "publish"))

    has_moderate_permission = has_publish_permission

    def has_advanced_settings_permission(self, request, user=None):
        return self.has_generic_permission(request, "advanced_settings", user)

    def has_change_permissions_permission(self, request, user=None):
        """
        Has user ability to change permissions for current page?
        """
        return self.has_generic_permission(request, "change_permissions", user)

    def has_add_permission(self, request, user=None):
        """
        Has user ability to add page under current page?
        """
        return self.has_generic_permission(request, "add", user)

    def has_move_page_permission(self, request, user=None):
        """Has user ability to move current page?
        """
        return self.has_generic_permission(request, "move_page", user)

    def has_generic_permission(self, request, perm_type, user=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if not user:
            user = request.user
        att_name = "permission_%s_cache" % perm_type
        if (not hasattr(self, "permission_user_cache")
                or not hasattr(self, att_name)
                or user.pk != self.permission_user_cache.pk):
            from cms.utils.permissions import has_generic_permission

            self.permission_user_cache = user
            setattr(self, att_name, has_generic_permission(
                self.pk, user, perm_type, self.site_id))
            if getattr(self, att_name):
                self.permission_edit_cache = True
        return getattr(self, att_name)

    def get_media_path(self, filename):
        """
        Returns path (relative to MEDIA_ROOT/MEDIA_URL) to directory for storing
        page-scope files. This allows multiple pages to contain files with
        identical names without namespace issues. Plugins such as Picture can
        use this method to initialise the 'upload_to' parameter for File-based
        fields. For example:
            image = models.ImageField(
                _("image"), upload_to=CMSPlugin.get_media_path)

        where CMSPlugin.get_media_path calls self.page.get_media_path

        This location can be customised using the CMS_PAGE_MEDIA_PATH setting
        """
        return join(get_cms_setting('PAGE_MEDIA_PATH'), "%d" % self.pk, filename)

    def reload(self):
        """
        Reload a page from the database
        """
        return Page.objects.get(pk=self.pk)

    def get_object_queryset(self):
        """Returns smart queryset depending on object type - draft / public
        """
        qs = self.__class__.objects
        return (self.publisher_is_draft and qs.drafts() or qs.public().published())

    def _publisher_can_publish(self):
        """Is parent of this object already published?
        """
        if self.parent_id:
            try:
                return bool(self.parent.publisher_public_id)
            except AttributeError:
                raise PublisherCantPublish
        return True

    def get_previous_filtered_sibling(self, **filters):
        filters.update({
            'publisher_is_draft': self.publisher_is_draft
        })
        filters.update({
            'site__id': self.site_id
        })
        try:
            return self.get_siblings().filter(path__lt=self.path, **filters).reverse()[0]
        except IndexError:
            return None

    def get_next_filtered_sibling(self, **filters):
        filters.update({
            'publisher_is_draft': self.publisher_is_draft
        })
        filters.update({
            'site__id': self.site_id
        })
        try:
            return self.get_siblings().filter(path__gt=self.path, **filters)[0]
        except IndexError:
            return None

    def _publisher_save_public(self, obj):
        """Mptt specific stuff before the object can be saved, overrides
        original publisher method.

        Args:
            obj - public variant of `self` to be saved.

        """
        if self.parent_id and self.parent.publisher_public_id:
            assert self.parent_id == self.parent.pk
            public_parent = Page.objects.get(pk=self.parent.publisher_public_id)
        else:
            public_parent = None
        filters = dict(publisher_public__isnull=False)
        if public_parent:
            filters['publisher_public__parent__in'] = [public_parent]
        else:
            filters['publisher_public__parent__isnull'] = True
        prev_sibling = self.get_previous_filtered_sibling(**filters)
        public_prev_sib = (prev_sibling.publisher_public if prev_sibling else None)

        if not self.publisher_public_id:  # first time published
            # is there anybody on left side?
            if not self.parent_id:
                obj.parent_id = None
                self.add_sibling(pos='right', instance=obj)
            else:
                if public_prev_sib:
                    obj.parent_id = public_prev_sib.parent_id
                    public_prev_sib.add_sibling(pos='right', instance=obj)
                else:
                    if public_parent:
                        obj.parent_id = public_parent.pk
                        obj.parent = public_parent
                        obj = obj.add_root(instance=obj)
                        obj = obj.move(target=public_parent, pos='first-child')
        else:
            # check if object was moved / structural tree change
            prev_public_sibling = obj.get_previous_filtered_sibling()
            if self.depth != obj.depth or \
                            public_parent != obj.parent or \
                            public_prev_sib != prev_public_sibling:
                if public_prev_sib:
                    # We've got a sibling on the left side (previous)
                    obj.parent_id = public_prev_sib.parent_id
                    obj.save()

                    if obj.parent_id:
                        # The draft page (self) has been moved under
                        # another page.
                        # So move the live page (obj) to be a sibling
                        # of the public closest sibling (public_prev_sib).
                        obj = obj.move(public_prev_sib, pos="right")
                    else:
                        # The draft page (self) has been moved to the root
                        # so move the public page (obj) to be a sibling
                        # of the draft page (self).
                        # This keeps the tree paths consistent by making sure
                        # the public page (obj) has a greater path than
                        # the draft page.
                        obj = obj.move(self, pos="right")
                elif public_parent:
                    # move as a first child to parent
                    obj.parent_id = public_parent.pk
                    obj.save()
                    obj = obj.move(target=public_parent, pos='first-child')
                else:
                    # it is a move from the right side or just save
                    next_sibling = self.get_next_filtered_sibling(**filters)
                    if next_sibling and next_sibling.publisher_public_id:
                        obj.parent_id = next_sibling.parent_id
                        obj.save()
                        obj = obj.move(next_sibling.publisher_public, pos="left")
            else:
                obj.save()
        return obj

    def move(self, target, pos=None):
        super(Page, self).move(target, pos)
        return self.reload()

    def rescan_placeholders(self):
        """
        Rescan and if necessary create placeholders in the current template.
        """
        # inline import to prevent circular imports
        from cms.models.placeholdermodel import Placeholder
        from cms.utils.placeholder import get_placeholders

        placeholders = get_placeholders(self.get_template())
        found = {}
        for placeholder in self.placeholders.all():
            if placeholder.slot in placeholders:
                found[placeholder.slot] = placeholder
        for placeholder_name in placeholders:
            if placeholder_name not in found:
                placeholder = Placeholder.objects.create(slot=placeholder_name)
                self.placeholders.add(placeholder)
                found[placeholder_name] = placeholder
        return found

    def get_xframe_options(self):
        """ Finds X_FRAME_OPTION from tree if inherited """
        xframe_options = get_xframe_cache(self)
        if xframe_options is None:
            xframe_options = self.xframe_options
            if not xframe_options or xframe_options == self.X_FRAME_OPTIONS_INHERIT:
                ancestors = self.get_ancestors()

                # Ignore those pages which just inherit their value
                ancestors = ancestors.exclude(xframe_options=self.X_FRAME_OPTIONS_INHERIT)

                # Now just give me the clickjacking setting (not anything else)
                xframe_options = list(reversed(ancestors.values_list('xframe_options', flat=True)))
                if self.xframe_options != self.X_FRAME_OPTIONS_INHERIT:
                    xframe_options.append(self.xframe_options)
                if len(xframe_options) <= 0:
                    # No ancestors were found
                    return None

                xframe_options = xframe_options[0]
            set_xframe_cache(self, xframe_options)

        return xframe_options

    def undo(self):
        """
        Revert the current page to the previous revision
        """
        from cms.utils.reversion_hacks import reversion, Revision

        # Get current reversion version by matching the reversion_id for the page
        versions = reversion.get_for_object(self)
        if self.revision_id:
            current_revision = Revision.objects.get(pk=self.revision_id)
        else:
            try:
                current_version = versions[0]
            except IndexError as e:
                e.message = "no current revision found"
                raise
            current_revision = current_version.revision
        try:
            previous_version = versions.filter(revision__pk__lt=current_revision.pk)[0]
        except IndexError as e:
            e.message = "no previous revision found"
            raise
        previous_revision = previous_version.revision

        clean = self._apply_revision(previous_revision)
        return Page.objects.get(pk=self.pk), clean

    def redo(self):
        """
        Revert the current page to the next revision
        """
        from cms.utils.reversion_hacks import reversion, Revision

        # Get current reversion version by matching the reversion_id for the page
        versions = reversion.get_for_object(self)
        if self.revision_id:
            current_revision = Revision.objects.get(pk=self.revision_id)
        else:
            try:
                current_version = versions[0]
            except IndexError as e:
                e.message = "no current revision found"
                raise
            current_revision = current_version.revision
        try:
            previous_version = versions.filter(revision__pk__gt=current_revision.pk).order_by('pk')[0]
        except IndexError as e:
            e.message = "no next revision found"
            raise
        next_revision = previous_version.revision

        clean = self._apply_revision(next_revision)
        return Page.objects.get(pk=self.pk), clean

    def _apply_revision(self, target_revision, set_dirty=False):
        """
        Revert to a specific revision
        """
        from cms.models.pluginmodel import CMSPlugin
        from cms.utils.page_resolver import is_valid_url

        # Get current titles
        old_titles = list(self.title_set.all())

        # remove existing plugins / placeholders in the current page version
        placeholder_ids = self.placeholders.all().values_list('pk', flat=True)
        plugins = CMSPlugin.objects.filter(placeholder__in=placeholder_ids).order_by('-depth')
        for plugin in plugins:
            plugin._no_reorder = True
            plugin.delete()
        self.placeholders.all().delete()

        # populate the page status data from the target version
        target_revision.revert(delete=True)
        rev_page = get_object_or_404(Page, pk=self.pk)
        rev_page.revision_id = target_revision.pk
        rev_page.publisher_public_id = self.publisher_public_id
        rev_page.save()

        # cleanup placeholders
        new_placeholders = rev_page.placeholders.all()
        slots = {}
        for new_ph in new_placeholders:
            if not new_ph.slot in slots:
                slots[new_ph.slot] = new_ph
            else:
                if new_ph in placeholder_ids:
                    new_ph.delete()
                elif slots[new_ph.slot] in placeholder_ids:
                    slots[new_ph.slot].delete()

        # check reverted titles for slug collisions
        new_titles = rev_page.title_set.all()
        clean = True
        for title in new_titles:
            try:
                is_valid_url(title.path, rev_page)
            except ValidationError:
                for old_title in old_titles:
                    if old_title.language == title.language:
                        title.slug = old_title.slug
                        title.save()
                        clean = False
            if set_dirty:
                self.set_publisher_state(title.language, PUBLISHER_STATE_DIRTY)
        return clean


def _reversion():
    exclude_fields = [
        'publisher_is_draft',
        'publisher_public',
        'publisher_state',
    ]

    reversion_register(
        Page,
        follow=["title_set", "placeholders", "pagepermission_set"],
        exclude_fields=exclude_fields
    )


_reversion()

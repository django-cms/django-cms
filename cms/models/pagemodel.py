# -*- coding: utf-8 -*-
from logging import getLogger
from os.path import join

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.utils import six
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import get_language, ugettext_lazy as _

from cms import constants
from cms.cache.page import set_xframe_cache, get_xframe_cache
from cms.constants import PUBLISHER_STATE_DEFAULT, PUBLISHER_STATE_PENDING, PUBLISHER_STATE_DIRTY, TEMPLATE_INHERITANCE_MAGIC
from cms.exceptions import PublicIsUnmodifiable, PublicVersionNeeded, LanguageError
from cms.models.managers import PageManager
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
                .exclude(publisher_state=PUBLISHER_STATE_PENDING)
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
                    # moved to be set to the correct state.
                    moved_page.mark_as_published(language)
                    moved_page.mark_descendants_as_published(language)
                elif published:
                    # page is published but it's parent is not
                    # mark the page being moved (source) as "pending"
                    moved_page.mark_as_pending(language)
                    # mark all descendants of source as "pending"
                    moved_page.mark_descendants_pending(language)
            elif published:
                moved_page.mark_as_published(language)
                moved_page.mark_descendants_as_published(language)

        from cms.cache import invalidate_cms_page_cache
        invalidate_cms_page_cache()
        return moved_page

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
        from cms.models import Placeholder, Title

        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable("copy page is not allowed for public pages")

        titles = Title.objects.all()
        placeholders = Placeholder.objects.all()
        pages = self.get_descendants(True).order_by('path').iterator()
        site_reverse_ids = (
            Page
            .objects
            .filter(site=site, reverse_id__isnull=False)
            .values_list('reverse_id', flat=True)
        )
        pages_by_old_pk = {}

        def _do_copy(page, parent=None):
            origin_id = page.pk

            # create a copy of this page by setting pk = None (=new instance)
            page.pk = None
            page.path = None
            page.depth = None
            page.numchild = 0
            page.publisher_public_id = None
            page.is_home = False
            page.site = site

            parent = parent or pages_by_old_pk.get(page.parent_id)

            if parent:
                page.parent = parent
                page.parent_id = parent.pk
            else:
                page.parent = None
                page.parent_id = None

            # only set reverse_id on standard copy
            if page.reverse_id in site_reverse_ids:
                page.reverse_id = None
            page.save()

            # copy titles of this page
            for title in titles.filter(page=origin_id).iterator():
                title.pk = None  # setting pk = None creates a new instance
                title.page = page
                title.published = False
                # create slug-copy for standard copy
                title.slug = page_utils.get_available_slug(title)

                if title.publisher_public_id:
                    title.publisher_public = None
                title.save()

            # copy the placeholders (and plugins on those placeholders!)
            for ph in placeholders.filter(page=origin_id).iterator():
                plugins = ph.get_plugins_list()

                try:
                    ph = page.placeholders.get(slot=ph.slot)
                except Placeholder.DoesNotExist:
                    ph.pk = None  # make a new instance
                    ph.save()
                    page.placeholders.add(ph)
                if plugins:
                    copy_plugins_to(plugins, ph)

            # copy permissions if necessary
            if get_cms_setting('PERMISSION') and copy_permissions:
                from cms.models.permissionmodels import PagePermission

                permissions = PagePermission.objects.filter(page__id=origin_id)

                for permission in permissions.iterator():
                    permission.pk = None
                    permission.page = page
                    permission.save()

            extension_pool.copy_extensions(Page.objects.get(pk=origin_id), page)
            return page

        if position in ("first-child", "last-child"):
            parent = target
        elif target.parent_id:
            parent = target.parent
        else:
            parent = None

        old_page = next(pages)
        old_page_id = old_page.pk

        new_page = _do_copy(old_page, parent=parent)

        if target:
            new_page = new_page.move(target, pos=position)

        pages_by_old_pk[old_page_id] = new_page

        # loop over the rest of pages
        for child_page in pages:
            child_page_id = child_page.pk
            new_child_page = _do_copy(child_page)
            pages_by_old_pk[child_page_id] = new_child_page

        # invalidate the menu for this site
        menu_pool.clear(site_id=site.pk)
        return new_page

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
        from cms.utils.permissions import get_current_user

        user = get_current_user()

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

    def update(self, refresh=False, **fields):
        cls = self.__class__
        cls.objects.filter(pk=self.pk).update(**fields)

        if refresh:
            return self.reload()
        return

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

        # Publication can be successful but the page is not guaranteed
        # to be in the published state.
        # This happens if a parent of the page is not published,
        # so the page is marked as pending.
        marked_as_published = False

        if not self.pk:
            self.save()

        # be sure we have the newest data including tree information
        self.refresh_from_db()

        if self._publisher_can_publish():
            published = True

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

            # Sets the tree attributes and saves the public page
            public_page = self._publisher_save_public(public_page)

            if not public_page.pk:
                public_page.save()

            if not public_page.parent_id:
                # If we're publishing a page with no parent
                # automatically set it's status to published
                marked_as_published = True
            else:
                # The page has a parent so we fetch the published
                # status of the parent page.
                marked_as_published = public_page.parent.is_published(language)

            # The target page now has a pk, so can be used as a target
            self._copy_titles(public_page, language, marked_as_published)
            self._copy_contents(public_page, language)

            # trigger home update
            public_page.save()
            # invalidate the menu for this site
            menu_pool.clear(site_id=self.site_id)
            self.publisher_public = public_page
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

        if marked_as_published and get_cms_setting('PLACEHOLDER_CACHE'):
            # Only clear the placeholder cache if the page
            # was successfully published and is actually marked as published.
            for placeholder in self.publisher_public.get_placeholders():
                placeholder.clear_cache(language, site_id=self.site_id)
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
        assert self.publisher_is_draft

        public = self.get_public_object()

        if public and public.get_title_obj(language, fallback=False):
            state = public.get_publisher_state(language)
            # keep the same state
            # only set the page as unpublished
            public.set_publisher_state(
                language,
                state=state,
                published=False
            )

        if self.is_published(language) and self.get_publisher_state(language) == PUBLISHER_STATE_DEFAULT:
            # Only change the state if the draft page is published
            # and it's state is the default (0)
            self.set_publisher_state(language, state=PUBLISHER_STATE_PENDING)

    def mark_descendants_pending(self, language):
        assert self.publisher_is_draft

        descendants = self.get_descendants().filter(
            publisher_public__isnull=False,
            title_set__language=language,
        )

        for child in descendants.iterator():
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
            self.get_children()
            .filter(
                title_set__published=True,
                title_set__language=language
            )
            .select_related('publisher_public', 'publisher_public__parent')
            .order_by('path')
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

            if page.publisher_public:
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
                    draft_title = titles_by_page_id[page.pk]

                    if draft_title.publisher_state == PUBLISHER_STATE_PENDING:
                        (page
                         .title_set
                         .filter(pk=draft_title.pk)
                         .update(publisher_state=PUBLISHER_STATE_DEFAULT))

                    public_title = titles_by_page_id.get(page.publisher_public_id)

                    if public_title and not public_title.published:
                        (publisher_public
                         .title_set
                         .filter(pk=public_title.pk)
                         .update(published=True, publisher_state=PUBLISHER_STATE_DEFAULT))
                    page.mark_descendants_as_published(language)
            elif page.get_publisher_state(language) == PUBLISHER_STATE_PENDING:
                page.publish(language)

    def revert_to_live(self, language):
        """Revert the draft version to the same state as the public version
        """
        if not self.publisher_is_draft:
            # Revert can only be called on draft pages
            raise PublicIsUnmodifiable('The public instance cannot be reverted. Use draft.')

        if not self.publisher_public:
            raise PublicVersionNeeded('A public version of this page is needed')

        public = self.publisher_public
        public._copy_attributes(self)
        public._copy_contents(self, language)
        public._copy_titles(self, language, public.is_published(language))

        self.title_set.filter(language=language).update(
            published=True,
            publisher_state=PUBLISHER_STATE_DEFAULT,
        )

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

    def update_languages(self, languages):
        languages = ",".join(languages)
        # Update current instance
        self.languages = languages
        # Commit. It's important to not call save()
        # we'd like to commit only the languages field and without
        # any kind of signals.
        self.update(languages=languages)

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
        if not self.has_cached_descendants():
            self._cached_descendants = list(self.get_descendants())
        return self._cached_descendants

    def has_cached_descendants(self):
        return hasattr(self, "_cached_descendants")

    def set_translations_cache(self):
        translations = self.title_set.all()
        self._title_cache = {trans.language: trans for trans in translations.iterator()}

    # ## Title object access

    def get_title_obj(self, language=None, fallback=True, force_reload=False):
        """Helper function for accessing wanted / current title.
        If wanted title doesn't exists, EmptyTitle instance will be returned.
        """
        language = self._get_title_cache(language, fallback, force_reload)
        if language in self.title_cache:
            return self.title_cache[language]
        from cms.models.titlemodels import EmptyTitle

        return EmptyTitle(language)

    def get_title_obj_attribute(self, attrname, language=None, fallback=True, force_reload=False):
        """Helper function for getting attribute or None from wanted/current title.
        """
        try:
            attribute = getattr(self.get_title_obj(language, fallback, force_reload), attrname)
            return attribute
        except AttributeError:
            return None

    def get_path(self, language=None, fallback=True, force_reload=False):
        """
        get the path of the page depending on the given language
        """
        return self.get_title_obj_attribute("path", language, fallback, force_reload)

    def get_slug(self, language=None, fallback=True, force_reload=False):
        """
        get the slug of the page depending on the given language
        """
        return self.get_title_obj_attribute("slug", language, fallback, force_reload)

    def get_title(self, language=None, fallback=True, force_reload=False):
        """
        get the title of the page depending on the given language
        """
        return self.get_title_obj_attribute("title", language, fallback, force_reload)

    def get_menu_title(self, language=None, fallback=True, force_reload=False):
        """
        get the menu title of the page depending on the given language
        """
        menu_title = self.get_title_obj_attribute("menu_title", language, fallback, force_reload)
        if not menu_title:
            return self.get_title(language, True, force_reload)
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

    def get_changed_date(self, language=None, fallback=True, force_reload=False):
        """
        get when this page was last updated
        """
        return self.changed_date

    def get_changed_by(self, language=None, fallback=True, force_reload=False):
        """
        get user who last changed this page
        """
        return self.changed_by

    def get_page_title(self, language=None, fallback=True, force_reload=False):
        """
        get the page title of the page depending on the given language
        """
        page_title = self.get_title_obj_attribute("page_title", language, fallback, force_reload)

        if not page_title:
            return self.get_title(language, True, force_reload)
        return page_title

    def get_meta_description(self, language=None, fallback=True, force_reload=False):
        """
        get content for the description meta tag for the page depending on the given language
        """
        return self.get_title_obj_attribute("meta_description", language, fallback, force_reload)

    def get_application_urls(self, language=None, fallback=True, force_reload=False):
        """
        get application urls conf for application hook
        """
        return self.application_urls

    def get_redirect(self, language=None, fallback=True, force_reload=False):
        """
        get redirect
        """
        return self.get_title_obj_attribute("redirect", language, fallback, force_reload)

    def _get_title_cache(self, language, fallback, force_reload):
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

    def has_view_permission(self, user):
        from cms.utils.page_permissions import user_can_view_page
        return user_can_view_page(user, page=self)

    def get_view_restrictions(self):
        from cms.models import PagePermission

        page = self.get_draft_object()
        return PagePermission.objects.for_page(page=page).filter(can_view=True)

    def has_view_restrictions(self):
        if get_cms_setting('PERMISSION'):
            return self.get_view_restrictions().exists()
        return False

    def has_add_permission(self, user):
        """
        Has user ability to add page under current page?
        """
        from cms.utils.page_permissions import user_can_add_subpage
        return user_can_add_subpage(user, self)

    def has_change_permission(self, user):
        from cms.utils.page_permissions import user_can_change_page
        return user_can_change_page(user, page=self)

    def has_delete_permission(self, user):
        from cms.utils.page_permissions import user_can_delete_page
        return user_can_delete_page(user, page=self)

    def has_delete_translation_permission(self, user, language):
        from cms.utils.page_permissions import user_can_delete_page_translation
        return user_can_delete_page_translation(user, page=self, language=language)

    def has_publish_permission(self, user):
        from cms.utils.page_permissions import user_can_publish_page
        return user_can_publish_page(user, page=self)

    def has_advanced_settings_permission(self, user):
        from cms.utils.page_permissions import user_can_change_page_advanced_settings
        return user_can_change_page_advanced_settings(user, page=self)

    def has_change_permissions_permission(self, user):
        """
        Has user ability to change permissions for current page?
        """
        from cms.utils.page_permissions import user_can_change_page_permissions
        return user_can_change_page_permissions(user, page=self)

    def has_move_page_permission(self, user):
        """Has user ability to move current page?
        """
        from cms.utils.page_permissions import user_can_move_page
        return user_can_move_page(user, page=self)

    def has_placeholder_change_permission(self, user):
        if not self.publisher_is_draft:
            return False
        return self.has_change_permission(user)

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

    def get_filtered_siblings(self, **filters):
        filters.update({
            'publisher_is_draft': self.publisher_is_draft
        })
        filters.update({
            'site__id': self.site_id
        })
        return self.get_siblings().filter(**filters)

    def get_previous_filtered_sibling(self, **filters):
        siblings = self.get_filtered_siblings(path__lt=self.path, **filters)

        try:
            sibling = siblings.reverse()[0]
        except IndexError:
            sibling = None
        return sibling

    def get_left_sibling_pk(self):
        siblings = self.get_filtered_siblings(path__lt=self.path)

        try:
            sibling = siblings.values_list('pk', flat=True).reverse()[0]
        except IndexError:
            sibling = None
        return sibling

    def get_next_filtered_sibling(self, **filters):
        siblings = self.get_filtered_siblings(path__gt=self.path, **filters)

        try:
            sibling = siblings[0]
        except IndexError:
            sibling = None
        return sibling

    def get_right_sibling_pk(self):
        siblings = self.get_filtered_siblings(path__gt=self.path)

        try:
            sibling = siblings.values_list('pk', flat=True)[0]
        except IndexError:
            sibling = None
        return sibling

    def _publisher_save_public(self, obj):
        """Mptt specific stuff before the object can be saved, overrides
        original publisher method.

        Args:
            obj - public variant of `self` to be saved.

        """
        if self.parent_id and self.parent.publisher_public_id:
            public_parent = Page.objects.get(pk=self.parent.publisher_public_id)
        elif not self.parent_id:
            # The draft page (self) is in the root
            # so move the public page (obj) to be a sibling
            # of the draft page (self).
            # This keeps the tree paths consistent by making sure
            # the public page (obj) has a greater path than
            # the draft page.
            obj.parent = None
            obj.save()
            obj = obj.move(self, pos="right")
            return obj
        else:
            public_parent = None

        obj.parent = public_parent
        obj.save()

        if not public_parent:
            return obj

        # The draft page (self) has been moved under another page.
        # Or is already inside another page and it's been moved
        # to a different location in the same page tree.

        # The sibling page on the left side of the draft page being moved (self)
        left_sibling = self.get_previous_filtered_sibling(
            publisher_public__parent=public_parent,
        )

        # The sibling page on the right side of the draft page being moved (self)
        right_sibling = self.get_next_filtered_sibling(
            publisher_public__parent=public_parent,
        )

        if left_sibling:
            left_public_sibling_pk = obj.get_left_sibling_pk()
            left_sibling_changed = left_sibling.publisher_public_id != left_public_sibling_pk
        else:
            left_sibling_changed = False

        if right_sibling:
            right_public_sibling_pk = obj.get_right_sibling_pk()
            right_sibling_changed = right_sibling.publisher_public_id != right_public_sibling_pk
        else:
            right_sibling_changed = False

        first_time_published = not self.publisher_public_id
        parent_change = public_parent != obj.parent
        tree_change = self.depth != obj.depth or left_sibling_changed or right_sibling_changed

        if first_time_published or parent_change or tree_change:
            if left_sibling:
                # Moving sibling page from left to right
                obj = obj.move(left_sibling.publisher_public, pos="right")
            elif right_sibling:
                # Moving sibling page from right to left
                obj = obj.move(right_sibling.publisher_public, pos="left")
            else:
                obj = obj.move(target=public_parent, pos='first-child')
        return obj

    def move(self, target, pos=None):
        super(Page, self).move(target, pos)
        return self.reload()

    def rescan_placeholders(self):
        """
        Rescan and if necessary create placeholders in the current template.
        """
        existing = {}
        placeholders = [pl.slot for pl in self.get_declared_placeholders()]

        for placeholder in self.placeholders.all():
            if placeholder.slot in placeholders:
                existing[placeholder.slot] = placeholder

        for placeholder in placeholders:
            if placeholder not in existing:
                existing[placeholder] = self.placeholders.create(slot=placeholder)
        return existing

    def get_declared_placeholders(self):
        # inline import to prevent circular imports
        from cms.utils.placeholder import get_placeholders

        return get_placeholders(self.get_template())

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

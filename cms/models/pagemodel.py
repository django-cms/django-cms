# -*- coding: utf-8 -*-
from cms import constants
from cms.utils.conf import get_cms_setting
from django.core.exceptions import PermissionDenied
from cms.exceptions import NoHomeFound, PublicIsUnmodifiable
from cms.models.managers import PageManager, PagePermissionsPermissionManager
from cms.models.metaclasses import PageMetaClass
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.publisher.errors import MpttPublisherCantPublish
from cms.utils import i18n, urlutils, page as page_utils
from cms.utils import timezone
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.helpers import reversion_register
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language, ugettext_lazy as _
from menus.menu_pool import menu_pool
from mptt.models import MPTTModel
from os.path import join
from datetime import timedelta
import copy


class Page(MPTTModel):
    """
    A simple hierarchical page model
    """
    __metaclass__ = PageMetaClass
    LIMIT_VISIBILITY_IN_MENU_CHOICES = (
        (1, _('for logged in users only')),
        (2, _('for anonymous users only')),
    )
    PUBLISHER_STATE_DEFAULT = 0
    PUBLISHER_STATE_DIRTY = 1
    PUBLISHER_STATE_DELETE = 2
    # Page was marked published, but some of page parents are not.
    PUBLISHER_STATE_PENDING = 4

    template_choices = [(x, _(y)) for x, y in get_cms_setting('TEMPLATES')]

    created_by = models.CharField(_("created by"), max_length=70, editable=False)
    changed_by = models.CharField(_("changed by"), max_length=70, editable=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    changed_date = models.DateTimeField(auto_now=True)

    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_('When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True, help_text=_('When to expire the page. Leave empty to never expire.'), db_index=True)
    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(_("soft root"), db_index=True, default=False, help_text=_("All ancestors will not be displayed in the navigation"))
    reverse_id = models.CharField(_("id"), max_length=40, db_index=True, blank=True, null=True, help_text=_("An unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("attached menu"), max_length=80, db_index=True, blank=True, null=True)
    published = models.BooleanField(_("is published"), blank=True)

    template = models.CharField(_("template"), max_length=100, choices=template_choices, help_text=_('The template used to render the content.'))
    site = models.ForeignKey(Site, help_text=_('The site the page is accessible at.'), verbose_name=_("site"))

    login_required = models.BooleanField(_("login required"), default=False)
    limit_visibility_in_menu = models.SmallIntegerField(_("menu visibility"), default=None, null=True, blank=True, choices=LIMIT_VISIBILITY_IN_MENU_CHOICES, db_index=True, help_text=_("limit when this page is visible in the menu"))

    level = models.PositiveIntegerField(db_index=True, editable=False)
    lft = models.PositiveIntegerField(db_index=True, editable=False)
    rght = models.PositiveIntegerField(db_index=True, editable=False)
    tree_id = models.PositiveIntegerField(db_index=True, editable=False)

    # Placeholders (plugins)
    placeholders = models.ManyToManyField(Placeholder, editable=False)

    # Publisher fields
    moderator_state = models.SmallIntegerField(_('moderator state'), default=0, blank=True, editable=False)
    publisher_is_draft = models.BooleanField(default=1, editable=False, db_index=True)
    # This is misnamed - the one-to-one relation is populated on both ends
    publisher_public = models.OneToOneField('self', related_name='publisher_draft', null=True, editable=False)
    publisher_state = models.SmallIntegerField(default=0, editable=False, db_index=True)

    # Managers
    objects = PageManager()
    permissions = PagePermissionsPermissionManager()

    class Meta:
        permissions = (
            ('view_page', 'Can view page'),
            ('publish_page', 'Can publish page'),
        )
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('tree_id', 'lft')
        app_label = 'cms'

    class PublisherMeta:
        exclude_fields_append = ['id', 'publisher_is_draft', 'publisher_public',
                                 'publisher_state', 'moderator_state',
                                 'placeholders', 'lft', 'rght', 'tree_id',
                                 'parent']

    def __unicode__(self):
        title = self.get_menu_title(fallback=True)
        if title is None:
            title = u""
        return unicode(title)

    def is_dirty(self):
        return self.publisher_state == self.PUBLISHER_STATE_DIRTY

    def get_absolute_url(self, language=None, fallback=True):
        if self.is_home():
            return reverse('pages-root')
        path = self.get_path(language, fallback) or self.get_slug(language, fallback)
        return reverse('pages-details-by-slug', kwargs={"slug": path})

    def move_page(self, target, position='first-child'):
        """
        Called from admin interface when page is moved. Should be used on
        all the places which are changing page position. Used like an interface
        to mptt, but after move is done page_moved signal is fired.

        Note for issue #1166: url conflicts are handled by updated
        check_title_slugs, overwrite_url on the moved page don't need any check
        as it remains the same regardless of the page position in the tree
        """
        # make sure move_page does not break when using INHERIT template
        # and moving to a top level position
        if (position in ('left', 'right')
            and not target.parent
            and self.template == constants.TEMPLATE_INHERITANCE_MAGIC):
            self.template = self.get_template()
        self.move_to(target, position)

        # fire signal
        from cms.models.moderatormodels import PageModeratorState
        from cms.utils import moderator
        import cms.signals as cms_signals
        cms_signals.page_moved.send(sender=Page, instance=self)  # titles get saved before moderation
        self.save()  # always save the page after move, because of publisher
        moderator.page_changed(self, force_moderation_action=PageModeratorState.ACTION_MOVE)
        # check the slugs
        page_utils.check_title_slugs(self)

    def _copy_titles(self, target):
        """
        Copy all the titles to a new page (which must have a pk).
        :param target: The page where the new titles should be stored
        """
        old_titles = dict(target.title_set.values_list('language', 'pk'))
        for title in self.title_set.all():
            # If an old title exists, overwrite. Otherwise create new
            title.pk = old_titles.pop(title.language, None)
            title.page = target
            title.save()
        if old_titles:
            from titlemodels import Title
            Title.objects.filter(id__in=old_titles.values()).delete()

    def _copy_contents(self, target):
        """
        Copy all the plugins to a new page.
        :param target: The page where the new content should be stored
        """
        # TODO: Make this into a "graceful" copy instead of deleting and overwriting
        # copy the placeholders (and plugins on those placeholders!)
        CMSPlugin.objects.filter(placeholder__page=target).delete()
        for ph in self.placeholders.all():
            plugins = ph.get_plugins_list()
            try:
                ph = target.placeholders.get(slot=ph.slot)
            except Placeholder.DoesNotExist:
                ph.pk = None  # make a new instance
                ph.save()
                target.placeholders.add(ph)
                # update the page copy
            if plugins:
                copy_plugins_to(plugins, ph)

    def _copy_attributes(self, target):
        """
        Copy all page data to the target. This excludes parent and other values
        that are specific to an exact instance.
        :param target: The Page to copy the attributes to
        """
        target.publication_date = self.publication_date
        target.publication_end_date = self.publication_end_date
        target.in_navigation = self.in_navigation
        target.login_required = self.login_required
        target.limit_visibility_in_menu = self.limit_visibility_in_menu
        target.soft_root = self.soft_root
        target.reverse_id = self.reverse_id
        target.navigation_extenders = self.navigation_extenders
        target.template = self.template
        target.site_id = self.site_id

    def copy_page(self, target, site, position='first-child',
                  copy_permissions=True):
        """
        Copy a page [ and all its descendants to a new location ]
        Doesn't checks for add page permissions anymore, this is done in PageAdmin.

        Note: public_copy was added in order to enable the creation of a copy
        for creating the public page during the publish operation as it sets the
        publisher_is_draft=False.

        Note for issue #1166: when copying pages there is no need to check for
        conflicting URLs as pages are copied unpublished.
        """
        from cms.utils.moderator import update_moderation_message

        page_copy = None

        pages = [self] + list(self.get_descendants().order_by('-rght'))

        site_reverse_ids = Page.objects.filter(site=site, reverse_id__isnull=False).values_list('reverse_id', flat=True)

        if target:
            target.old_pk = -1
            if position == "first-child":
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
        # loop over all affected pages (self is included in descendants)
        for page in pages:
            titles = list(page.title_set.all())
            # get all current placeholders (->plugins)
            placeholders = list(page.placeholders.all())
            origin_id = page.id
            # create a copy of this page by setting pk = None (=new instance)
            page.old_pk = page.pk
            page.pk = None
            page.level = None
            page.rght = None
            page.lft = None
            page.tree_id = None
            page.published = False
            page.publisher_public_id = None
            # only set reverse_id on standard copy
            if page.reverse_id in site_reverse_ids:
                page.reverse_id = None
            if first:
                first = False
                if tree:
                    page.parent = tree[0]
                else:
                    page.parent = None
                page.insert_at(target, position)
            else:
                count = 1
                found = False
                for prnt in tree:
                    if prnt.old_pk == page.parent_id:
                        page.parent = prnt
                        tree = tree[0:count]
                        found = True
                        break
                    count += 1
                if not found:
                    page.parent = None
            tree.append(page)
            page.site = site

            page.save()

            # copy permissions if necessary
            if get_cms_setting('PERMISSION') and copy_permissions:
                from cms.models.permissionmodels import PagePermission
                for permission in PagePermission.objects.filter(page__id=origin_id):
                    permission.pk = None
                    permission.page = page
                    permission.save()

            update_moderation_message(page, unicode(_('Page was copied.')))

            # copy titles of this page
            for title in titles:
                title.pk = None  # setting pk = None creates a new instance
                title.page = page

                # create slug-copy for standard copy
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
                    # update the page copy
                    page_copy = page
                if plugins:
                    copy_plugins_to(plugins, ph)

        # invalidate the menu for this site
        menu_pool.clear(site_id=site.pk)
        return page_copy  # return the page_copy or None

    def save(self, no_signals=False, commit=True, **kwargs):
        """
        Args:
            commit: True if model should be really saved
        """

        # delete template cache
        if hasattr(self, '_template_cache'):
            delattr(self, '_template_cache')

        created = not bool(self.pk)
        # Published pages should always have a publication date
        # if the page is published we set the publish date if not set yet.
        if self.publication_date is None and self.published:
            self.publication_date = timezone.now() - timedelta(seconds=5)

        if self.reverse_id == "":
            self.reverse_id = None

        from cms.utils.permissions import _thread_locals
        user = getattr(_thread_locals, "user", None)
        if user:
            self.changed_by = user.username
        else:
            self.changed_by = "script"
        if created:
            self.created_by = self.changed_by

        if commit:
            if no_signals:  # ugly hack because of mptt
                self.save_base(cls=self.__class__, **kwargs)
            else:
                super(Page, self).save(**kwargs)

    def save_base(self, *args, **kwargs):
        """Overridden save_base. If an instance is draft, and was changed, mark
        it as dirty.

        Dirty flag is used for changed nodes identification when publish method
        takes place. After current changes are published, state is set back to
        PUBLISHER_STATE_DEFAULT (in publish method).
        """
        keep_state = getattr(self, '_publisher_keep_state', None)

        if self.publisher_is_draft and not keep_state:
            self.publisher_state = self.PUBLISHER_STATE_DIRTY
        if keep_state:
            delattr(self, '_publisher_keep_state')

        ret = super(Page, self).save_base(*args, **kwargs)
        return ret

    def publish(self):
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
        if not self.parent_id:
            self.clear_home_pk_cache()
        if self._publisher_can_publish():
            if self.publisher_public_id:
                # Ensure we have up to date mptt properties
                public_page = Page.objects.get(pk=self.publisher_public_id)
            else:
                public_page = Page(created_by=self.created_by)

            self._copy_attributes(public_page)
            # we need to set relate this new public copy to its draft page (self)
            public_page.publisher_public = self
            public_page.publisher_is_draft = False

            # Ensure that the page is in the right position and save it
            public_page = self._publisher_save_public(public_page)
            public_page.published = (public_page.parent_id is None or public_page.parent.published)
            public_page.save()

            # The target page now has a pk, so can be used as a target
            self._copy_titles(public_page)
            self._copy_contents(public_page)

            # invalidate the menu for this site
            menu_pool.clear(site_id=self.site_id)

            # taken from Publisher - copy_page needs to call self._publisher_save_public(copy) for mptt insertion
            # insert_at() was maybe calling _create_tree_space() method, in this
            # case may tree_id change, so we must update tree_id from db first
            # before save
            if getattr(self, 'tree_id', None):
                me = self._default_manager.get(pk=self.pk)
                self.tree_id = me.tree_id

            self.publisher_public = public_page
            published = True
        else:
            # Nothing left to do
            pass

        if self.publisher_public and self.publisher_public.published:
            self.publisher_state = Page.PUBLISHER_STATE_DEFAULT
        else:
            self.publisher_state = Page.PUBLISHER_STATE_PENDING

        self.published = True
        self._publisher_keep_state = True
        self.save()
        # If we are publishing, this page might have become a "home" which
        # would change the path
        if self.is_home():
            for title in self.title_set.all():
                if title.path != '':
                    title.save()

        # clean moderation log
        self.pagemoderatorstate_set.all().delete()

        if not published:
            # was not published, escape
            return

        # Check if there are some children which are waiting for parents to
        # become published.
        publish_set = self.get_descendants().filter(published=True).select_related('publisher_public')
        for page in publish_set:
            if page.publisher_public:
                if page.publisher_public.parent.published:
                    if not page.publisher_public.published:
                        page.publisher_public.published = True
                        page.publisher_public.save()
                    if page.publisher_state == Page.PUBLISHER_STATE_PENDING:
                        page.publisher_state = Page.PUBLISHER_STATE_DEFAULT
                        page._publisher_keep_state = True
                        page.save()
            elif page.publisher_state == Page.PUBLISHER_STATE_PENDING:
                page.publish()

        # fire signal after publishing is done
        import cms.signals as cms_signals
        cms_signals.post_publish.send(sender=Page, instance=self)

        return published

    def unpublish(self):
        """
        Removes this page from the public site
        :returns: True if this page was successfully unpublished
        """
        # Publish can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be unpublished. Use draft.')

        # First, make sure we are in the correct state
        self.published = False
        self.save()
        public_page = self.get_public_object()
        if public_page:
            public_page.published = False
            public_page.save()

            # Go through all children of our public instance
            descendants = public_page.get_descendants()
            for child in descendants:
                child.published = False
                child.save()
                draft = child.publisher_public
                if (draft and draft.published and
                        draft.publisher_state == Page.PUBLISHER_STATE_DEFAULT):
                    draft.publisher_state = Page.PUBLISHER_STATE_PENDING
                    draft._publisher_keep_state = True
                    draft.save()

        return True

    def revert(self):
        """Revert the draft version to the same state as the public version
        """
        # Revert can only be called on draft pages
        if not self.publisher_is_draft:
            raise PublicIsUnmodifiable('The public instance cannot be reverted. Use draft.')
        if not self.publisher_public:
            # TODO: Issue an error
            return

        public = self.publisher_public
        public._copy_titles(self)
        if self.parent != (self.publisher_public.parent_id and
                           self.publisher_public.parent.publisher_draft):
            # We don't send the signals here
            self.move_to(public.parent.publisher_draft)
        public._copy_contents(self)
        public._copy_attributes(self)
        self.published = True
        self.publisher_state = self.PUBLISHER_STATE_DEFAULT
        self._publisher_keep_state = True
        self.save()
        # clean moderation log
        self.pagemoderatorstate_set.all().delete()

    def delete(self):
        """Mark public instance for deletion and delete draft.
        """
        placeholders = self.placeholders.all()

        for ph in placeholders:
            plugin = CMSPlugin.objects.filter(placeholder=ph)
            plugin.delete()
            ph.delete()

        if self.publisher_public_id:
            # mark the public instance for deletion
            self.publisher_public.publisher_state = self.PUBLISHER_STATE_DELETE
            self.publisher_public.save()
        super(Page, self).delete()

    def delete_with_public(self):
        """
        Assuming this page and all its descendants have been marked for
        deletion, recursively deletes the entire set of pages including the
        public instance.
        """
        descendants = list(self.get_descendants().order_by('level'))
        descendants.reverse()
        # TODO: Use a better exception class - PermissionDenied is not quite right
        for page in descendants:
            if not page.delete_requested():
                raise PermissionDenied('There are descendant pages not marked for deletion')
        descendants.append(self)

        # Get all pages that are children of any public page that would be deleted
        public_children = Page.objects.public().filter(
            parent__publisher_public__in=descendants)
        public_pages = Page.objects.public().filter(publisher_public__in=descendants)
        if set(public_children).difference(public_pages):
            raise PermissionDenied('There are pages that would be orphaned. '
                                   'Publish their move requests first.')

        for page in descendants:
            placeholders = list(page.placeholders.all())
            if page.publisher_public_id:
                placeholders = placeholders + list(page.publisher_public.placeholders.all())

            plugins = CMSPlugin.objects.filter(placeholder__in=placeholders)
            plugins.delete()
            for ph in placeholders:
                ph.delete()
            if page.publisher_public_id:
                page.publisher_public.delete()
            super(Page, page).delete()

    def get_draft_object(self):
        if not self.publisher_is_draft:
            return self.publisher_draft
        return self

    def get_public_object(self):
        if not self.publisher_is_draft:
            return self
        return self.publisher_public

    def get_languages(self):
        """
        get the list of all existing languages for this page
        """
        from cms.models.titlemodels import Title

        if not hasattr(self, "all_languages"):
            self.all_languages = Title.objects.filter(page=self).values_list("language", flat=True).distinct()
            self.all_languages = list(self.all_languages)
            self.all_languages.sort()
            self.all_languages = map(str, self.all_languages)
        return self.all_languages

    def get_cached_ancestors(self, ascending=True):
        if ascending:
            if not hasattr(self, "ancestors_ascending"):
                self.ancestors_ascending = list(self.get_ancestors(ascending))
            return self.ancestors_ascending
        else:
            if not hasattr(self, "ancestors_descending"):
                self.ancestors_descending = list(self.get_ancestors(ascending))
            return self.ancestors_descending

    # ## Title object access

    def get_title_obj(self, language=None, fallback=True, version_id=None, force_reload=False):
        """Helper function for accessing wanted / current title.
        If wanted title doesn't exists, EmptyTitle instance will be returned.
        """
        language = self._get_title_cache(language, fallback, version_id, force_reload)
        if language in self.title_cache:
            return self.title_cache[language]
        from cms.models.titlemodels import EmptyTitle
        return EmptyTitle()

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

    def get_meta_keywords(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get content for the keywords meta tag for the page depending on the given language
        """
        return self.get_title_obj_attribute("meta_keywords", language, fallback, version_id, force_reload)

    def get_application_urls(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get application urls conf for application hook
        """
        return self.get_title_obj_attribute("application_urls", language, fallback, version_id, force_reload)

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
        elif not language in self.title_cache:
            if fallback:
                fallback_langs = i18n.get_fallback_languages(language)
                for lang in fallback_langs:
                    if lang in self.title_cache:
                        return lang
            load = True
        if load:
            from cms.models.titlemodels import Title
            if version_id:
                from reversion.models import Version
                version = get_object_or_404(Version, pk=version_id)
                revs = [related_version.object_version for related_version in version.revision.version_set.all()]
                for rev in revs:
                    obj = rev.object
                    if obj.__class__ == Title:
                        self.title_cache[obj.language] = obj
            else:
                title = Title.objects.get_title(self, language, language_fallback=fallback)
                if title:
                    self.title_cache[title.language] = title
                language = title.language
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
                    template = self.get_ancestors(ascending=True).exclude(
                        template=constants.TEMPLATE_INHERITANCE_MAGIC).values_list('template', flat=True)[0]
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

    def has_view_permission(self, request):
        from cms.models.permissionmodels import PagePermission, GlobalPagePermission
        from cms.utils.plugins import current_site

        if not self.publisher_is_draft:
            return self.publisher_draft.has_view_permission(request)
        # does any restriction exist?
        # inherited and direct
        is_restricted = PagePermission.objects.for_page(page=self).filter(can_view=True).exists()
        if request.user.is_authenticated():
            site = current_site(request)
            global_perms_q = Q(can_view=True) & Q(
                Q(sites__in=[site]) | Q(sites__isnull=True)
            )
            global_view_perms = GlobalPagePermission.objects.with_user(
                request.user).filter(global_perms_q).exists()

            # a global permission was given to the request's user
            if global_view_perms:
                return True

            elif not is_restricted:
                if ((get_cms_setting('PUBLIC_FOR') == 'all') or
                    (get_cms_setting('PUBLIC_FOR') == 'staff' and
                     request.user.is_staff)):
                    return True

            # a restricted page and an authenticated user
            elif is_restricted:
                opts = self._meta
                codename = '%s.view_%s' % (opts.app_label, opts.object_name.lower())
                user_perm = request.user.has_perm(codename)
                generic_perm = self.has_generic_permission(request, "view")
                return (user_perm or generic_perm)

        else:
            #anonymous user
            if is_restricted or not get_cms_setting('PUBLIC_FOR') == 'all':
                # anyonymous user, page has restriction and global access is permitted
                return False
            else:
                # anonymous user, no restriction saved in database
                return True
        # Authenticated user
        # Django wide auth perms "can_view" or cms auth perms "can_view"
        opts = self._meta
        codename = '%s.view_%s' % (opts.app_label, opts.object_name.lower())
        return (request.user.has_perm(codename) or
                self.has_generic_permission(request, "view"))

    def has_change_permission(self, request):
        opts = self._meta
        if request.user.is_superuser:
            return True
        return request.user.has_perm(opts.app_label + '.' + opts.get_change_permission()) and \
            self.has_generic_permission(request, "change")

    def has_delete_permission(self, request):
        opts = self._meta
        if request.user.is_superuser:
            return True
        return request.user.has_perm(opts.app_label + '.' + opts.get_delete_permission()) and \
            self.has_generic_permission(request, "delete")

    def has_publish_permission(self, request):
        if request.user.is_superuser:
            return True
        opts = self._meta
        return request.user.has_perm(opts.app_label + '.' + "publish_page") and \
            self.has_generic_permission(request, "publish")
    has_moderate_permission = has_publish_permission

    def has_advanced_settings_permission(self, request):
        return self.has_generic_permission(request, "advanced_settings")

    def has_change_permissions_permission(self, request):
        """
        Has user ability to change permissions for current page?
        """
        return self.has_generic_permission(request, "change_permissions")

    def has_add_permission(self, request):
        """
        Has user ability to add page under current page?
        """
        return self.has_generic_permission(request, "add")

    def has_move_page_permission(self, request):
        """Has user ability to move current page?
        """
        return self.has_generic_permission(request, "move_page")

    def has_generic_permission(self, request, perm_type):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        att_name = "permission_%s_cache" % perm_type
        if not hasattr(self, "permission_user_cache") or not hasattr(self, att_name) \
                or request.user.pk != self.permission_user_cache.pk:
            from cms.utils.permissions import has_generic_permission
            self.permission_user_cache = request.user
            setattr(self, att_name, has_generic_permission(
                    self.id, request.user, perm_type, self.site_id))
            if getattr(self, att_name):
                self.permission_edit_cache = True
        return getattr(self, att_name)

    def is_home(self):
        if self.parent_id:
            return False
        else:
            try:
                return self.home_pk_cache == self.pk
            except NoHomeFound:
                pass
        return False

    def get_home_pk_cache(self):
        attr = "%s_home_pk_cache_%s" % (self.publisher_is_draft and "draft" or "public", self.site_id)
        if getattr(self, attr, None) is None:
            setattr(self, attr, self.get_object_queryset().get_home(self.site).pk)
        return getattr(self, attr)

    def set_home_pk_cache(self, value):

        attr = "%s_home_pk_cache_%s" % (self.publisher_is_draft and "draft" or "public", self.site_id)
        setattr(self, attr, value)
    home_pk_cache = property(get_home_pk_cache, set_home_pk_cache)

    def clear_home_pk_cache(self):
        self.home_pk_cache = None

    def get_media_path(self, filename):
        """
        Returns path (relative to MEDIA_ROOT/MEDIA_URL) to directory for storing page-scope files.
        This allows multiple pages to contain files with identical names without namespace issues.
        Plugins such as Picture can use this method to initialise the 'upload_to' parameter for
        File-based fields. For example:
            image = models.ImageField(_("image"), upload_to=CMSPlugin.get_media_path)
        where CMSPlugin.get_media_path calls self.page.get_media_path

        This location can be customised using the CMS_PAGE_MEDIA_PATH setting
        """
        return join(get_cms_setting('PAGE_MEDIA_PATH'), "%d" % self.id, filename)

    def last_page_states(self):
        """Returns last five page states, if they exist, optimized, calls sql
        query only if some states available
        """
        result = getattr(self, '_moderator_state_cache', None)
        if result is None:
            result = list(self.pagemoderatorstate_set.all().order_by('created'))
            self._moderator_state_cache = result
        return result[:5]

    def delete_requested(self):
        """ Checks whether there are any delete requests for this page.
        Uses the same cache as last_page_states to minimize DB requests
        """
        from cms.models import PageModeratorState
        result = getattr(self, '_moderator_state_cache', None)
        if result is None:
            return self.pagemoderatorstate_set.get_delete_actions().exists()
        for state in result:
            if state.action == PageModeratorState.ACTION_DELETE:
                return True
        return False

    def is_public_published(self):
        """Returns true if public model is published.
        """
        if hasattr(self, '_public_published_cache'):
            # if it was cached in change list, return cached value
            return self._public_published_cache
        # If we have a public version it will be published as well.
        # If it isn't published, it should be deleted.
        return self.published and self.publisher_public_id and self.publisher_public.published

    def reload(self):
        """
        Reload a page from the database
        """
        return Page.objects.get(pk=self.pk)

    def get_object_queryset(self):
        """Returns smart queryset depending on object type - draft / public
        """
        qs = self.__class__.objects
        return self.publisher_is_draft and qs.drafts() or qs.public().published()

    def _publisher_can_publish(self):
        """Is parent of this object already published?
        """
        if self.parent_id:
            try:
                return bool(self.parent.publisher_public_id)
            except AttributeError:
                raise MpttPublisherCantPublish
        return True

    def get_next_filtered_sibling(self, **filters):
        """Very similar to original mptt method, but adds support for filters.
        Returns this model instance's next sibling in the tree, or
        ``None`` if it doesn't have a next sibling.
        """
        opts = self._mptt_meta
        if self.is_root_node():
            filters.update({
                '%s__isnull' % opts.parent_attr: True,
                '%s__gt' % opts.tree_id_attr: getattr(self, opts.tree_id_attr),
            })
        else:
            filters.update({
                 opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr),
                '%s__gt' % opts.left_attr: getattr(self, opts.right_attr),
            })

        # publisher stuff
        filters.update({
            'publisher_is_draft': self.publisher_is_draft
        })
        # multisite
        filters.update({
            'site__id': self.site_id
        })

        sibling = None
        try:
            sibling = self._tree_manager.filter(**filters)[0]
        except IndexError:
            pass
        return sibling

    def get_previous_filtered_sibling(self, **filters):
        """Very similar to original mptt method, but adds support for filters.
        Returns this model instance's previous sibling in the tree, or
        ``None`` if it doesn't have a previous sibling.
        """
        opts = self._mptt_meta
        if self.is_root_node():
            filters.update({
                '%s__isnull' % opts.parent_attr: True,
                '%s__lt' % opts.tree_id_attr: getattr(self, opts.tree_id_attr),
            })
            order_by = '-%s' % opts.tree_id_attr
        else:
            filters.update({
                 opts.parent_attr: getattr(self, '%s_id' % opts.parent_attr),
                '%s__lt' % opts.right_attr: getattr(self, opts.left_attr),
            })
            order_by = '-%s' % opts.right_attr

        # publisher stuff
        filters.update({
            'publisher_is_draft': self.publisher_is_draft
        })
        # multisite
        filters.update({
            'site__id': self.site_id
        })

        sibling = None
        try:
            sibling = self._tree_manager.filter(**filters).order_by(order_by)[0]
        except IndexError:
            pass
        return sibling

    def _publisher_save_public(self, obj):
        """Mptt specific stuff before the object can be saved, overrides original
        publisher method.

        Args:
            obj - public variant of `self` to be saved.

        """
        public_parent = self.parent.publisher_public if self.parent_id else None
        filters = dict(publisher_public__isnull=False)
        if public_parent:
            filters['publisher_public__parent__in'] = [public_parent]
        else:
            filters['publisher_public__parent__isnull'] = True
        prev_sibling = self.get_previous_filtered_sibling(**filters)
        public_prev_sib = prev_sibling.publisher_public if prev_sibling else None

        if not self.publisher_public_id:  # first time published
            # is there anybody on left side?
            if public_prev_sib:
                obj.insert_at(public_prev_sib, position='right', save=False)
            else:
                if public_parent:
                    obj.insert_at(public_parent, position='first-child', save=False)
        else:
            # check if object was moved / structural tree change
            prev_public_sibling = obj.get_previous_filtered_sibling()
            if self.level != obj.level or \
                public_parent != obj.parent or \
                public_prev_sib != prev_public_sibling:
                if public_prev_sib:
                    obj.move_to(public_prev_sib, position="right")
                elif public_parent:
                    # move as a first child to parent
                    obj.move_to(public_parent, position='first-child')
                else:
                    # it is a move from the right side or just save
                    next_sibling = self.get_next_filtered_sibling(**filters)
                    if next_sibling and next_sibling.publisher_public_id:
                        obj.move_to(next_sibling.publisher_public, position="left")

        return obj

    def rescan_placeholders(self):
        """
        Rescan and if necessary create placeholders in the current template.
        """
        # inline import to prevent circular imports
        from cms.utils.plugins import get_placeholders
        placeholders = get_placeholders(self.get_template())
        found = {}
        for placeholder in self.placeholders.all():
            if placeholder.slot in placeholders:
                found[placeholder.slot] = placeholder
        for placeholder_name in placeholders:
            if not placeholder_name in found:
                placeholder = Placeholder.objects.create(slot=placeholder_name)
                self.placeholders.add(placeholder)
                found[placeholder_name] = placeholder


def _reversion():
    exclude_fields = ['publisher_is_draft', 'publisher_public', 'publisher_state']

    reversion_register(
        Page,
        follow=["title_set", "placeholders", "pagepermission_set"],
        exclude_fields=exclude_fields
    )
_reversion()

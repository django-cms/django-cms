from os.path import join
from datetime import datetime
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _, get_language, ugettext
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from publisher import MpttPublisher
from publisher.errors import PublisherCantPublish
from cms.utils.urlutils import urljoin
from cms.models.managers import PageManager, PagePermissionsPermissionManager

from cms.utils.page import get_available_slug, check_title_slugs
from cms.exceptions import NoHomeFound
from cms.utils.helpers import reversion_register
from cms.utils.i18n import get_fallback_languages
from menus.menu_pool import menu_pool
from django.utils.functional import lazy

class Page(MpttPublisher):
    """
    A simple hierarchical page model
    """
    MODERATOR_CHANGED = 0
    MODERATOR_NEED_APPROVEMENT = 1
    MODERATOR_NEED_DELETE_APPROVEMENT = 2
    MODERATOR_APPROVED = 10
    # special case - page was approved, but some of page parents if not approved yet
    MODERATOR_APPROVED_WAITING_FOR_PARENTS = 11
    
    moderator_state_choices = (
        (MODERATOR_CHANGED, _('changed')),
        (MODERATOR_NEED_APPROVEMENT, _('req. app.')),
        (MODERATOR_NEED_DELETE_APPROVEMENT, _('delete')),
        (MODERATOR_APPROVED, _('approved')),
        (MODERATOR_APPROVED_WAITING_FOR_PARENTS, _('app. par.')),
    )
    
    template_choices = [(x, _(y)) for x,y in settings.CMS_TEMPLATES]
    
    created_by = models.CharField(_("created by"), max_length=70, editable=False)
    changed_by = models.CharField(_("changed by"), max_length=70, editable=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    creation_date = models.DateTimeField(editable=False, default=datetime.now)
    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_('When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True, help_text=_('When to expire the page. Leave empty to never expire.'), db_index=True)
    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(_("soft root"), db_index=True, default=False, help_text=_("All ancestors will not be displayed in the navigation"))
    reverse_id = models.CharField(_("id"), max_length=40, db_index=True, blank=True, null=True, help_text=_("An unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("attached menu"), max_length=80, db_index=True, blank=True, null=True)
    published = models.BooleanField(_("is published"), blank=True)
    
    template = models.CharField(_("template"), max_length=100, choices=template_choices, help_text=_('The template used to render the content.'))
    site = models.ForeignKey(Site, help_text=_('The site the page is accessible at.'), verbose_name=_("site"))
    
    moderator_state = models.SmallIntegerField(_('moderator state'), choices=moderator_state_choices, default=MODERATOR_NEED_APPROVEMENT, blank=True)
    
    level = models.PositiveIntegerField(db_index=True, editable=False)
    lft = models.PositiveIntegerField(db_index=True, editable=False)
    rght = models.PositiveIntegerField(db_index=True, editable=False)
    tree_id = models.PositiveIntegerField(db_index=True, editable=False)
    
    login_required = models.BooleanField(_("login required"),default=False)
    menu_login_required = models.BooleanField(_("menu login required"),default=False, help_text=_("only show this page in the menu if the user is logged in"))
    
    # Managers
    objects = PageManager()
    permissions = PagePermissionsPermissionManager()

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('tree_id', 'lft')
        app_label = 'cms'
    
    class PublisherMeta:
        exclude_fields_append = ['moderator_state']
    
    def __unicode__(self):
        title = self.get_menu_title(fallback=True)
        if title is None:
            title = u""
        pre_title = settings.CMS_TITLE_CHARACTER * self.level
        return u'%s%s' % (pre_title, title)
    
    def move_page(self, target, position='first-child'):
        """Called from admin interface when page is moved. Should be used on
        all the places which are changing page position. Used like an interface
        to mptt, but after move is done page_moved signal is fired.
        """
        self.move_to(target, position)
        
        # fire signal
        from cms.models.moderatormodels import PageModeratorState
        self.force_moderation_action = PageModeratorState.ACTION_MOVE
        import cms.signals as cms_signals
        cms_signals.page_moved.send(sender=Page, instance=self) #titles get saved before moderation
        self.save(change_state=True) # always save the page after move, because of publisher
        
        # check the slugs
        check_title_slugs(self)
        
        
    def copy_page(self, target, site, position='first-child', copy_permissions=True, copy_moderation=True):
        """
        copy a page and all its descendants to a new location
        
        Doesn't checks for add page permissions anymore, this is done in PageAdmin.
        """
        from cms.utils.moderator import update_moderation_message
        
        descendants = [self] + list(self.get_descendants().order_by('-rght'))
        site_reverse_ids = [ x[0] for x in Page.objects.filter(site=site, reverse_id__isnull=False).values_list('reverse_id') ]
        if target:
            target.old_pk = -1
            if position == "first_child":
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
        for page in descendants:
           
            titles = list(page.title_set.all())
            plugins = list(page.cmsplugin_set.all().order_by('tree_id', '-rght'))
            origin_id = page.id
            page.old_pk = page.pk
            page.pk = None
            page.level = None
            page.rght = None
            page.lft = None
            page.tree_id = None
            page.published = False
            page.publisher_status = Page.MODERATOR_CHANGED
            page.publisher_public_id = None
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
            # copy moderation, permissions if necessary
            if settings.CMS_PERMISSION and copy_permissions:
                from cms.models.permissionmodels import PagePermission
                for permission in PagePermission.objects.filter(page__id=origin_id):
                    permission.pk = None
                    permission.page = page
                    permission.save()
            if settings.CMS_MODERATOR and copy_moderation:
                from cms.models.moderatormodels import PageModerator
                for moderator in PageModerator.objects.filter(page__id=origin_id):
                    moderator.pk = None
                    moderator.page = page
                    moderator.save()
            update_moderation_message(page, unicode(_('Page was copied.')))
            for title in titles:
                title.pk = None
                title.publisher_public_id = None
                title.published = False
                title.page = page
                title.slug = get_available_slug(title)
                title.save()
            ptree = []
            for p in plugins:
                try:
                    plugin, cls = p.get_plugin_instance()
                except KeyError: #plugin type not found anymore
                    continue
                p.page = page
                p.pk = None
                p.id = None
                p.tree_id = None
                p.lft = None
                p.rght = None
                p.inherited_public_id = None
                p.publisher_public_id = None
                if p.parent:
                    pdif = p.level - ptree[-1].level
                    if pdif < 0:
                        ptree = ptree[:pdif-1]
                    p.parent = ptree[-1]
                    if pdif != 0:
                        ptree.append(p)
                else:
                    ptree = [p]
                p.level = None
                p.save()
                if plugin:
                    plugin.pk = p.pk
                    plugin.id = p.pk
                    plugin.page = page
                    plugin.tree_id = p.tree_id
                    plugin.lft = p.lft
                    plugin.rght = p.rght
                    plugin.level = p.level
                    plugin.cmsplugin_ptr = p
                    plugin.publisher_public_id = None
                    plugin.public_id = None
                    plugin.plubished = False
                    plugin.save()
    
    def save(self, no_signals=False, change_state=True, commit=True, force_with_moderation=False, force_state=None, **kwargs):
        """
        Args:
            
            commit: True if model should be really saved
            force_with_moderation: can be true when new object gets added under 
                some existing page and this new page will require moderation; 
                this is because of how this adding works - first save, then move
        """
        
        # Published pages should always have a publication date
        publish_directly, under_moderation = False, False
        
        if self.publisher_is_draft:
            # publisher specific stuff, but only on draft model, this is here 
            # because page initializes publish process
            
            if settings.CMS_MODERATOR:
                under_moderation = force_with_moderation or self.pk and bool(self.get_moderator_queryset().count())
            
            created = not bool(self.pk)
            if settings.CMS_MODERATOR:
                if change_state:
                    if created:
                        # new page....
                        self.moderator_state = Page.MODERATOR_CHANGED
                    elif not self.requires_approvement():
                        # always change state to need approvement when there is some change
                        self.moderator_state = Page.MODERATOR_NEED_APPROVEMENT
                    
                    if not under_moderation and (self.published or self.publisher_public):
                        # existing page without moderator - publish it directly if 
                        # published is True
                        publish_directly = True
                    
            elif change_state:
                self.moderator_state = Page.MODERATOR_CHANGED
                #publish_directly = True - no publisher, no publishing!! - we just
                # use draft models in this case
            
            if force_state is not None:
                self.moderator_state = force_state
            
        # if the page is published we set the publish date if not set yet.
        if self.publication_date is None and self.published:
            self.publication_date = datetime.now()
        
        if self.reverse_id == "":
            self.reverse_id = None
        
        from cms.utils.permissions import _thread_locals
        user = getattr(_thread_locals, "user", None)
        if user:
            self.changed_by = user.username
        else:
            self.changed_by = "script"
        if not self.pk:
            self.created_by = self.changed_by 
        
        if commit:
            if no_signals:# ugly hack because of mptt
                super(Page, self).save_base(cls=self.__class__, **kwargs)
            else:
                super(Page, self).save(**kwargs)
        
        #if commit and (publish_directly or created and not under_moderation):
        if self.publisher_is_draft and commit and publish_directly:
            self.publish()
            # post_publish signal moved to end of publish method()

    def get_calculated_status(self):
        """
        get the calculated status of the page based on published_date,
        published_end_date, and status
        """
        if settings.CMS_SHOW_START_DATE:
            if self.publication_date > datetime.now():
                return False
        
        if settings.CMS_SHOW_END_DATE and self.publication_end_date:
            if self.publication_end_date < datetime.now():
                return True

        return self.published
    calculated_status = property(get_calculated_status)
        
    def get_languages(self):
        """
        get the list of all existing languages for this page
        """
        from cms.models.titlemodels import Title

        if not hasattr(self, "all_languages"):
            self.all_languages = Title.objects.filter(page=self).values_list("language", flat=True).distinct()
            self.all_languages = list(self.all_languages)
            self.all_languages.sort()    
        return self.all_languages

    def get_absolute_url(self, language=None, fallback=True):
        try:
            if self.is_home():
                return reverse('pages-root')
        except NoHomeFound:
            pass
        if settings.CMS_FLAT_URLS:
            path = self.get_slug(language, fallback)
        else:
            path = self.get_path(language, fallback)
            if hasattr(self, "home_cut_cache") and self.home_cut_cache:
                if not self.get_title_obj_attribute("has_url_overwrite", language, fallback) and path:
                    path = "/".join(path.split("/")[1:])
            else:    
                home_pk = None
                try:
                    home_pk = self.home_pk_cache
                except NoHomeFound:
                    pass
                ancestors = self.get_cached_ancestors(ascending=True)
                if self.parent_id and ancestors[-1].pk == home_pk and not self.get_title_obj_attribute("has_url_overwrite", language, fallback) and path:
                    path = "/".join(path.split("/")[1:])
            
        if settings.CMS_DBGETTEXT and settings.CMS_DBGETTEXT_SLUGS:
            path = '/'.join([ugettext(p) for p in path.split('/')])

        return urljoin(reverse('pages-root'), path)
    
    def get_cached_ancestors(self, ascending=True):
        if ascending:
            if not hasattr(self, "ancestors_ascending"):
                self.ancestors_ascending = list(self.get_ancestors(ascending)) 
            return self.ancestors_ascending
        else:
            if not hasattr(self, "ancestors_descending"):
                self.ancestors_descending = list(self.get_ancestors(ascending))
            return self.ancestors_descending
    
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
            if attribute and settings.CMS_DBGETTEXT:
                if attrname in ('slug', 'path') and \
                        not settings.CMS_DBGETTEXT_SLUGS:
                    return attribute
                return ugettext(attribute)
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
                fallback_langs = get_fallback_languages(language)
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
        template = None
        if self.template and len(self.template)>0 and \
            self.template != settings.CMS_TEMPLATE_INHERITANCE_MAGIC:
            template = self.template
        else:
            for p in self.get_ancestors(ascending=True):
                template = p.get_template()
                break
        if not template:
            template = settings.CMS_TEMPLATES[0][0]
        return template

    def get_template_name(self):
        """
        get the textual name (2nd parameter in settings.CMS_TEMPLATES)
        of the template of this page or of the nearest
        ancestor. failing to find that, return the name of the default template.
        """
        template = self.get_template()
        for t in settings.CMS_TEMPLATES:
            if t[0] == template:
                return t[1] 
        return _("default")

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
        return self.has_generic_permission(request, "publish")
    
    def has_advanced_settings_permission(self, request):
        return self.has_generic_permission(request, "advanced_settings")
    
    def has_change_permissions_permission(self, request):
        """Has user ability to change permissions for current page?
        """
        return self.has_generic_permission(request, "change_permissions")
    
    def has_add_permission(self, request):
        """Has user ability to add page under current page?
        """
        return self.has_generic_permission(request, "add")
    
    def has_move_page_permission(self, request):
        """Has user ability to move current page?
        """
        return self.has_generic_permission(request, "move_page")
    
    def has_moderate_permission(self, request):
        """Has user ability to moderate current page? If moderation isn't 
        installed, nobody can moderate.
        """
        if not settings.CMS_MODERATOR:
            return False
        return self.has_generic_permission(request, "moderate")
    
    def has_generic_permission(self, request, type):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        att_name = "permission_%s_cache" % type
        if not hasattr(self, "permission_user_cache") or not hasattr(self, att_name) \
            or request.user.pk != self.permission_user_cache.pk:
            from cms.utils.permissions import has_generic_permission
            self.permission_user_cache = request.user
            setattr(self, att_name, has_generic_permission(self.id, request.user, type, self.site_id))
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
        attr = "%s_home_pk_cache" % (self.publisher_is_draft and "draft" or "public")
        if not hasattr(self, attr):
            setattr(self, attr, self.get_object_queryset().get_home().pk)
        return getattr(self, attr)

    
    def set_home_pk_cache(self, value):
        attr = "%s_home_pk_cache" % (self.publisher_is_draft and "draft" or "public")
        setattr(self, attr, value)
    
    home_pk_cache = property(get_home_pk_cache, set_home_pk_cache)
    
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
        return join(settings.CMS_PAGE_MEDIA_PATH, "%d" % self.id, filename)
    
    def last_page_states(self):
        """Returns last five page states, if they exist, optimized, calls sql
        query only if some states available
        """
        # TODO: optimize SQL... 1 query per page 
        if settings.CMS_MODERATOR:
            has_moderator_state = getattr(self, '_has_moderator_state_chache', None)
            if has_moderator_state == False:
                return None
            return self.pagemoderatorstate_set.all().order_by('created',)[:5]
        return None
    
    def get_moderator_queryset(self):
        """Returns ordered set of all PageModerator instances, which should 
        moderate this page
        """
        from cms.models.moderatormodels import PageModerator
        if not settings.CMS_MODERATOR or not self.tree_id:
            return PageModerator.objects.get_empty_query_set()
        
        q = Q(page__tree_id=self.tree_id, page__level__lt=self.level, moderate_descendants=True) | \
            Q(page__tree_id=self.tree_id, page__level=self.level - 1, moderate_children=True) | \
            Q(page__pk=self.pk, moderate_page=True)
        
        return PageModerator.objects.distinct().filter(q).order_by('page__level')
    
    def is_under_moderation(self):
        return bool(self.get_moderator_queryset().count())
    
    def is_approved(self):
        """Returns true, if page is approved and published, or approved, but
        parents are missing..
        """
        return self.moderator_state in (Page.MODERATOR_APPROVED, Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
    
    def publish(self):
        """Overrides Publisher method, because there may be some descendants, which
        are waiting for parent to publish, so publish them if possible. 
        
        IMPORTANT: @See utils.moderator.approve_page for publishing permissions
        
        Returns: True if page was successfully published.
        """
        if not settings.CMS_MODERATOR:
            return
        
        # publish, but only if all parents are published!!
        published = None
        
        try:
            published = super(Page, self).publish()
            self.moderator_state = Page.MODERATOR_APPROVED
        except PublisherCantPublish:
            self.moderator_state = Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS
            
        self.save(change_state=False)
        if not published:
            # was not published, escape
            return
        
        # clean moderation log
        self.pagemoderatorstate_set.all().delete()
            
        # page was published, check if there are some childs, which are waiting
        # for publishing (because of the parent)
        publish_set = self.children.filter(moderator_state = Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS)
        for page in publish_set:
            # recursive call to all childrens....
            page.moderator_state = Page.MODERATOR_APPROVED
            page.save(change_state=False)
            page.publish()
        
        # fire signal after publishing is done
        import cms.signals as cms_signals
        cms_signals.post_publish.send(sender=Page, instance=self)
        return published
    
    def is_public_published(self):
        """Returns true if public model is published.
        """
        if hasattr(self, 'public_published_cache'):
            # if it was cached in change list, return cached value
            return self.public_published_cache
        # othervise make db lookup
        if self.publisher_public_id:
            return self.publisher_public.published
        #return is_public_published(self)
        return False
        
    def requires_approvement(self):
        return self.moderator_state in (Page.MODERATOR_NEED_APPROVEMENT, Page.MODERATOR_NEED_DELETE_APPROVEMENT)
    
    def get_moderation_value(self, user):
        """Returns page moderation value for given user, moderation value is
        sum of moderations.
        """
        moderation_value = getattr(self, '_moderation_value_cahce', None)
        if moderation_value is not None and self._moderation_value_cache_for_user_id == user.pk:
            return moderation_value
        try:
            page_moderator = self.pagemoderator_set.get(user=user)
        except ObjectDoesNotExist:
            return 0
        
        moderation_value = page_moderator.get_decimal()
        
        self._moderation_value_cahce = moderation_value
        self._moderation_value_cache_for_user_id = user
            
        return moderation_value 
        
reversion_register(Page, follow=["title_set", "cmsplugin_set", "pagepermission_set"])

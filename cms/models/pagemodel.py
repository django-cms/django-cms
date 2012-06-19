# -*- coding: utf-8 -*-
from cms.exceptions import NoHomeFound
from cms.models.managers import PageManager, PagePermissionsPermissionManager
from cms.models.metaclasses import PageMetaClass
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.publisher.errors import MpttPublisherCantPublish
from cms.utils import i18n, urlutils, page as page_utils
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.helpers import reversion_register
from datetime import datetime
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.translation import get_language, ugettext_lazy as _
from menus.menu_pool import menu_pool
from mptt.models import MPTTModel
from os.path import join
import copy






class Page(MPTTModel):
    """
    A simple hierarchical page model
    """
    __metaclass__ = PageMetaClass
    MODERATOR_CHANGED = 0
    MODERATOR_NEED_APPROVEMENT = 1
    MODERATOR_NEED_DELETE_APPROVEMENT = 2
    MODERATOR_APPROVED = 10
    # special case - page was approved, but some of page parents are not approved yet
    MODERATOR_APPROVED_WAITING_FOR_PARENTS = 11
    
    moderator_state_choices = (
        (MODERATOR_CHANGED, _('changed')),
        (MODERATOR_NEED_APPROVEMENT, _('req. app.')),
        (MODERATOR_NEED_DELETE_APPROVEMENT, _('delete')),
        (MODERATOR_APPROVED, _('approved')),
        (MODERATOR_APPROVED_WAITING_FOR_PARENTS, _('app. par.')),
    )
    
    LIMIT_VISIBILITY_IN_MENU_CHOICES = (
        (1,_('for logged in users only')),
        (2,_('for anonymous users only')),
    )
    PUBLISHER_STATE_DEFAULT = 0
    PUBLISHER_STATE_DIRTY = 1
    PUBLISHER_STATE_DELETE = 2
    
    template_choices = [(x, _(y)) for x,y in settings.CMS_TEMPLATES]
    
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
    
    moderator_state = models.SmallIntegerField(_('moderator state'), choices=moderator_state_choices, default=MODERATOR_NEED_APPROVEMENT, blank=True)
    
    level = models.PositiveIntegerField(db_index=True, editable=False)
    lft = models.PositiveIntegerField(db_index=True, editable=False)
    rght = models.PositiveIntegerField(db_index=True, editable=False)
    tree_id = models.PositiveIntegerField(db_index=True, editable=False)
    
    login_required = models.BooleanField(_("login required"), default=False)
    limit_visibility_in_menu = models.SmallIntegerField(_("menu visibility"), default=None, null=True, blank=True, choices=LIMIT_VISIBILITY_IN_MENU_CHOICES, db_index=True, help_text=_("limit when this page is visible in the menu"))
    
    # Placeholders (plugins)
    placeholders = models.ManyToManyField(Placeholder, editable=False)
    
    # Publisher fields

    publisher_is_draft = models.BooleanField(default=1, editable=False, db_index=True)
    publisher_public = models.OneToOneField('self', related_name='publisher_draft',  null=True, editable=False)
    publisher_state = models.SmallIntegerField(default=0, editable=False, db_index=True)
    
    # Managers
    objects = PageManager()
    permissions = PagePermissionsPermissionManager()

    class Meta:
        permissions = (
            ('view_page', 'Can view page'),
        )
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('site','tree_id', 'lft')
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
        return u'%s' % (title,)

    def get_absolute_url(self, language=None, fallback=True):
        if self.is_home():
            return reverse('pages-root')
        if settings.CMS_FLAT_URLS:
            path = self.get_slug(language, fallback)
            return urlutils.urljoin(reverse('pages-root'), path)
        # else
        path = self.get_path(language, fallback)
        return urlutils.urljoin(reverse('pages-root'), path)
    
    def move_page(self, target, position='first-child'):
        """Called from admin interface when page is moved. Should be used on
        all the places which are changing page position. Used like an interface
        to mptt, but after move is done page_moved signal is fired.
        """
        # make sure move_page does not break when using INHERIT template
        if (position in ('left', 'right')
            and not target.parent
            and self.template == settings.CMS_TEMPLATE_INHERITANCE_MAGIC):
            self.template = self.get_template()
        self.move_to(target, position)
        
        # fire signal
        from cms.models.moderatormodels import PageModeratorState
        self.force_moderation_action = PageModeratorState.ACTION_MOVE
        import cms.signals as cms_signals
        cms_signals.page_moved.send(sender=Page, instance=self) #titles get saved before moderation
        self.save(change_state=True) # always save the page after move, because of publisher
        
        # check the slugs
        page_utils.check_title_slugs(self)
        
    def copy_page(self, target, site, position='first-child',
                  copy_permissions=True, copy_moderation=True,
                  public_copy=False):
        """
        copy a page [ and all its descendants to a new location ]
        Doesn't checks for add page permissions anymore, this is done in PageAdmin.
        
        Note: public_copy was added in order to enable the creation of a copy for creating the public page during
        the publish operation as it sets the publisher_is_draft=False.
        """
        from cms.utils.moderator import update_moderation_message
        
        page_copy = None
        
        
        if public_copy:
            # create a copy of the draft page - existing code loops through pages so added it to a list 
            pages = [copy.copy(self)]            
        else:
            pages = [self] + list(self.get_descendants().order_by('-rght'))
            
        if not public_copy:    
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
            page.moderator_state = Page.MODERATOR_CHANGED
            page.publisher_public_id = None
            # only set reverse_id on standard copy
            if not public_copy:
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
             
            # override default page settings specific for public copy
            if public_copy:
                page.published = True
                page.publisher_is_draft=False
                page.moderator_state = Page.MODERATOR_APPROVED
                # we need to set relate this new public copy to its draft page (self)
                page.publisher_public = self
                
                # code taken from Publisher publish() overridden here as we need to save the page
                # before we are able to use the page object for titles, placeholders etc.. below
                # the method has been modified to return the object after saving the instance variable
                page = self._publisher_save_public(page)
                page_copy = page    # create a copy used in the return
            else:    
                # only need to save the page if it isn't public since it is saved above otherwise
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
                    
            # update moderation message for standard copy
            if not public_copy:
                update_moderation_message(page, unicode(_('Page was copied.')))
            
            # copy titles of this page
            for title in titles:
                title.pk = None # setting pk = None creates a new instance
                title.publisher_public_id = None
                title.published = False
                title.page = page
                
                # create slug-copy for standard copy
                if not public_copy:
                    title.slug = page_utils.get_available_slug(title)
                title.save()
                
            # copy the placeholders (and plugins on those placeholders!)
            for ph in placeholders:
                plugins = list(ph.cmsplugin_set.all().order_by('tree_id', '-rght'))
                try:
                    ph = page.placeholders.get(slot=ph.slot)
                except Placeholder.DoesNotExist:
                    ph.pk = None # make a new instance
                    ph.save()
                    page.placeholders.add(ph)
                    # update the page copy
                    page_copy = page
                if plugins:
                    copy_plugins_to(plugins, ph)
                    
        
        # invalidate the menu for this site
        menu_pool.clear(site_id=site.pk)
        return page_copy   # return the page_copy or None

    def save(self, no_signals=False, change_state=True, commit=True,
             force_with_moderation=False, force_state=None, **kwargs):
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
                self.save_base(cls=self.__class__, **kwargs)
            else:
                super(Page, self).save(**kwargs)
        
        #if commit and (publish_directly or created and not under_moderation):
        if self.publisher_is_draft:
            if self.published:
                if commit and publish_directly:
                    
                    self.publish()
                
    def save_base(self, *args, **kwargs):
        """Overriden save_base. If an instance is draft, and was changed, mark
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

        IMPORTANT: @See utils.moderator.approve_page for publishing permissions

        Returns: True if page was successfully published.
        """
        # Publish can only be called on moderated and draft pages
        if not self.publisher_is_draft:
            return

        # publish, but only if all parents are published!!
        published = None

        if not self.pk:
            self.save()

        if self._publisher_can_publish():
            ########################################################################
            # Assign the existing public page in old_public and mark it as
            # PUBLISHER_STATE_DELETE
            # the draft version was being deleted if I replaced the save()
            # below with a delete() directly so the deletion is handle at the end
            old_public = self.get_public_object()
            if old_public:
                old_public.publisher_state = self.PUBLISHER_STATE_DELETE
                # store old public on self, pass around instead
                self.old_public = old_public
                old_public.publisher_public = None  # remove the reference to the publisher_draft version of the page so it does not get deleted
                old_public.save()

            # we hook into the modified copy_page routing to do the heavy lifting of copying the draft page to a new public page
            new_public = self.copy_page(target=None, site=self.site,
                                        copy_moderation=False, position=None,
                                        copy_permissions=False, public_copy=True)

            # taken from Publisher - copy_page needs to call self._publisher_save_public(copy) for mptt insertion
            # insert_at() was maybe calling _create_tree_space() method, in this
            # case may tree_id change, so we must update tree_id from db first
            # before save
            if getattr(self, 'tree_id', None):
                me = self._default_manager.get(pk=self.pk)
                self.tree_id = me.tree_id

            self.published = True
            self.publisher_public = new_public
            self.moderator_state = Page.MODERATOR_APPROVED
            self.publisher_state = self.PUBLISHER_STATE_DEFAULT
            self._publisher_keep_state = True
            published = True
        else:
            self.moderator_state = Page.MODERATOR_APPROVED_WAITING_FOR_PARENTS

        self.save(change_state=False)

        if not published:
            # was not published, escape
            return

        # clean moderation log
        self.pagemoderatorstate_set.all().delete()

        # we delete the old public page - this only deletes the public page as we
        # have removed the old_public.publisher_public=None relationship to the draft page above
        if old_public:
            # reparent public child pages before delete so they don't get purged as well
            for child_page in old_public.children.order_by('lft'):
                child_page.move_to(new_public, 'last-child')
                child_page.save(change_state=False)
            # reload old_public to get correct tree attrs
            old_public = Page.objects.get(pk=old_public.pk)
            old_public.move_to(None, 'last-child')
            # moving the object out of the way berore deleting works, but why?
            # finally delete the old public page
            old_public.delete()

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
        
        placeholders = list(self.placeholders.all())
        if self.publisher_public_id:
            placeholders = placeholders + list(self.publisher_public.placeholders.all())
            
        for ph in placeholders:
            plugin = CMSPlugin.objects.filter(placeholder=ph)
            plugin.delete()
            ph.delete()
        if self.publisher_public_id:
            self.publisher_public.delete()
        super(Page, self).delete()
                        
    def get_draft_object(self):
        return self

    def get_public_object(self):
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
        template = None
        if self.template:
            if self.template != settings.CMS_TEMPLATE_INHERITANCE_MAGIC:
                template = self.template
            else:
                for p in self.get_ancestors(ascending=True):
                    template = p.get_template()
                    if template:
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
    
    def has_view_permission(self, request):
        from cms.models.permissionmodels import PagePermission, GlobalPagePermission
        from cms.utils.plugins import current_site
                        
        if not self.publisher_is_draft and self.publisher_public:
            return self.publisher_public.has_view_permission(request)
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
            	if ((settings.CMS_PUBLIC_FOR == 'all') or
            	    (settings.CMS_PUBLIC_FOR == 'staff' and
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
            if is_restricted or not settings.CMS_PUBLIC_FOR == 'all':
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
        return self.has_generic_permission(request, "publish")
    
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
    
    def has_moderate_permission(self, request):
        """
        Has user ability to moderate current page? If moderation isn't
        installed, nobody can moderate.
        """
        if not settings.CMS_MODERATOR:
            return False
        return self.has_generic_permission(request, "moderate")
    
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
        if not hasattr(self, attr):
            setattr(self, attr, self.get_object_queryset().get_home(self.site).pk)
        return getattr(self, attr)
    
    def set_home_pk_cache(self, value):
        attr = "%s_home_pk_cache_%s" % (self.publisher_is_draft and "draft" or "public", self.site_id)
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
                return self.pagemoderatorstate_set.none()
            return self.pagemoderatorstate_set.all().order_by('created',)[:5]
        return self.pagemoderatorstate_set.none()
    
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
    
    def reload(self):
        """
        Reload a page from the database
        """
        return Page.objects.get(pk=self.pk)
        
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

    def get_object_queryset(self):
        """Returns smart queryset depending on object type - draft / public
        """
        qs = self.__class__.objects
        return self.publisher_is_draft and qs.drafts() or qs.public()

    def _publisher_can_publish(self):
        """Is parent of this object already published?
        """
        if self.parent_id:
            try:
                return bool(self.parent.publisher_public_id)
            except AttributeError:
                raise MpttPublisherCantPublish
        return True

    def _publisher_get_public_copy(self):
        """This is here because of the relation between CMSPlugins - model
        inheritance.

        eg. Text.objects.get(pk=1).publisher_public returns instance of CMSPlugin
        instead of instance of Text, thats why this method must be overriden in
        CMSPlugin.
        """
        return self.publisher_public

    def get_next_filtered_sibling(self, **filters):
        """Very simillar to original mptt method, but adds support for filters.
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
        """Very simillar to original mptt method, but adds support for filters.
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
        prev_sibling = self.get_previous_filtered_sibling(publisher_public__isnull=False)

        if not self.publisher_public_id:
            # is there anybody on left side?
            if prev_sibling:
                obj.insert_at(prev_sibling.publisher_public, position='right', save=False)
            else:
                # it is a first time published object, perform insert_at:
                parent, public_parent = self.parent, None
                if parent:
                    public_parent = parent.publisher_public
                if public_parent:
                    obj.insert_at(public_parent, save=False)
        else:
            # check if object was moved / structural tree change
            prev_public_sibling = self.old_public.get_previous_filtered_sibling()

            if not self.level == self.old_public.level or \
                not (self.level > 0 and self.parent.publisher_public == self.old_public.parent) or \
                not prev_sibling == prev_public_sibling == None or \
                (prev_sibling and prev_sibling.publisher_public_id == prev_public_sibling.id):

                if prev_sibling:
                    obj.insert_at(prev_sibling.publisher_public, position="right")
                elif self.parent:
                    # move as a first child to parent
                    target = self.parent.publisher_public
                    obj.insert_at(target, position='first-child')
                else:
                    # it is a move from the right side or just save
                    next_sibling = self.get_next_filtered_sibling()
                    if next_sibling and next_sibling.publisher_public_id:
                        obj.insert_at(next_sibling.publisher_public, position="left")
            else:
                # insert at last public position
                prev_sibling = self.old_public.get_previous_filtered_sibling()

                if prev_sibling:
                    obj.insert_at(prev_sibling, position="right")
                elif self.old_public.parent:
                    # move as a first child to parent
                    target = self.old_public.parent
                    obj.insert_at(target, position='first-child')
                else:
                    # it is a move from the right side or just save
                    next_sibling = self.old_public.get_next_filtered_sibling()
                    if next_sibling and next_sibling.publisher_public_id:
                        obj.insert_at(next_sibling, position="left")
        # or none structural change, just save
        obj.save()
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

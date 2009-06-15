from datetime import datetime, date
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from os.path import join
from django.template.context import Context
import urllib2
from cms.urlutils import urljoin

import mptt
from cms import settings
from cms.models.managers import PageManager, PagePermissionManager, TitleManager
from cms.models import signals as cms_signals


if 'reversion' in settings.INSTALLED_APPS:
    import reversion

#try:
#    tagging = models.get_app('tagging')
#    from tagging.fields import TagField
#except ImproperlyConfigured:
#    tagging = False

#if not settings.CMS_TAGGING:
#    tagging = False

class Page(models.Model):
    """
    A simple hierarchical page model
    """
    # some class constants to refer to, e.g. Page.DRAFT
    DRAFT = 0
    PUBLISHED = 1
    EXPIRED = 2
    STATUSES = (
        (DRAFT, _('Draft')),
        (PUBLISHED, _('Published')),
    )
    author = models.ForeignKey(User, verbose_name=_("author"), limit_choices_to={'page__isnull' : False})
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    creation_date = models.DateTimeField(editable=False, default=datetime.now)
    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_('When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True, help_text=_('When to expire the page. Leave empty to never expire.'), db_index=True)
    login_required = models.BooleanField(_('login required'), default=False)
    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(_("soft root"), db_index=True, default=False, help_text=_("All ancestors will not be displayed in the navigation"))
    reverse_id = models.CharField(_("id"), max_length=40, db_index=True, blank=True, null=True, help_text=_("An unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("navigation extenders"), max_length=80, db_index=True, blank=True, null=True, choices=settings.CMS_NAVIGATION_EXTENDERS)
    status = models.IntegerField(_("status"), choices=STATUSES, default=DRAFT, db_index=True)
    template = models.CharField(_("template"), max_length=100, choices=settings.CMS_TEMPLATES, help_text=_('The template used to render the content.'))
    sites = models.ManyToManyField(Site, help_text=_('The site(s) the page is accessible at.'), verbose_name=_("sites"))
    
    # Managers
    objects = PageManager()

    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('tree_id', 'lft')
        
    def __unicode__(self):
        slug = self.get_slug(fallback=True)
        if slug is None:
            return u'' # otherwise we get unicode decode errors
        else:
            return slug
        
    
    def move_page(self, target, position='first-child'):
        """Called from admin interface when page is moved. Should be used on
        all the places which are changing page position. Used like an interface
        to mptt, but after move is done page_moved signal is fired.
        """
        self.move_to(target, position)
        # fire signal
        cms_signals.page_moved.send(sender=Page, instance=self)
        
    def copy_page(self, target, site, position='first-child'):
        """
        copy a page and all its descendants to a new location
        """
        descendants = [self] + list(self.get_descendants().filter(sites__pk=site.pk).order_by('-rght'))
        tree = [target]
        level_dif = self.level - target.level - 1
        first = True
        for page in descendants:
            new_level = page.level - level_dif
            dif = new_level - tree[-1].level 
            if dif < 0:
                tree = tree[:dif-1]
           
            titles = list(page.title_set.all())
            plugins = list(page.cmsplugin_set.all().order_by('tree_id', '-rght'))
            page.pk = None
            page.level = None
            page.rght = None
            page.lft = None
            page.tree_id = None
            page.status = Page.DRAFT
            page.parent = tree[-1]
            page.save()
            if first:
                first = False
                page.move_to(target, position)
            page.sites = [site]
            for title in titles:
                title.pk = None
                title.page = page
                title.save()
            ptree = []
            for p in plugins:
                plugin, cls = p.get_plugin_instance()
                p.page = page
                p.pk = None
                p.id = None
                p.tree_id = None
                p.lft = None
                p.rght = None
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
                    plugin.save()
            if dif != 0:
                tree.append(page)
    
    def save(self, no_signals=False):
        if not self.status:
            self.status = Page.DRAFT
        # Published pages should always have a publication date
        if self.publication_date is None and self.status == self.PUBLISHED:
            self.publication_date = datetime.now()
        # Drafts should not, unless they have been set to the future
        if self.status == Page.DRAFT:
            if settings.CMS_SHOW_START_DATE:
                if self.publication_date and self.publication_date <= datetime.now():
                    self.publication_date = None
            else:
                self.publication_date = None
        if self.reverse_id == "":
            self.reverse_id = None
        if no_signals:# ugly hack because of mptt
            super(Page, self).save_base(cls=self.__class__)
        else:
            super(Page, self).save()
            
    def get_calculated_status(self):
        """
        get the calculated status of the page based on published_date,
        published_end_date, and status
        """
        if settings.CMS_SHOW_START_DATE:
            if self.publication_date > datetime.now():
                return self.DRAFT
        
        if settings.CMS_SHOW_END_DATE and self.publication_end_date:
            if self.publication_end_date < datetime.now():
                return self.EXPIRED

        return self.status
    calculated_status = property(get_calculated_status)
        
    def get_languages(self):
        """
        get the list of all existing languages for this page
        """
        titles = Title.objects.filter(page=self)
        if not hasattr(self, "languages_cache"):
            languages = []
            for t in titles:
                if t.language not in languages:
                    languages.append(t.language)
            self.languages_cache = languages
        return self.languages_cache

    def get_absolute_url(self, language=None, fallback=True):
        if settings.CMS_FLAT_URLS:
            path = self.get_slug(language, fallback)
        else:
            path = self.get_path(language, fallback)
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
        self._get_title_cache(language, fallback, version_id, force_reload)
        if self.title_cache:
            return self.title_cache
        return EmptyTitle()
    
    def get_title_obj_attribute(self, attrname, language=None, fallback=True, version_id=None, force_reload=False):
        """Helper function for getting attribute or None from wanted/current title.
        """
        try:
            return getattr(self.get_title_obj(language, fallback, version_id, force_reload), attrname)
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
    
    def get_menu_title(self, language=None, fallback=False, version_id=None, force_reload=False):
        """
        get the menu title of the page depending on the given language
        """
        menu_title = self.get_title_obj_attribute("menu_title", language, fallback, version_id, force_reload)
        if not menu_title:
            return self.get_title(language, True, version_id, force_reload)
        return menu_title
    
    def get_page_title(self, language=None, fallback=False, version_id=None, force_reload=False):
        """
        get the page title of the page depending on the given language
        """
        page_title = self.get_title_obj_attribute("page_title", language, fallback, version_id, force_reload)
        if not page_title:
            return self.get_menu_title(language, True, version_id, force_reload)
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
        default_lang = False
        if not language:
            default_lang = True
            language = settings.CMS_DEFAULT_LANGUAGE
        load = False
        if not hasattr(self, "title_cache"):
            load = True
        elif self.title_cache and self.title_cache.language != language and language and not default_lang:
            load = True
        elif fallback and not self.title_cache:
            load = True 
        if force_reload:
            load = True
        if load:
            if version_id:
                from reversion.models import Version
                version = get_object_or_404(Version, pk=version_id)
                revs = [related_version.object_version for related_version in version.revision.version_set.all()]
                for rev in revs:
                    obj = rev.object
                    if obj.__class__ == Title:
                        if obj.language == language and obj.page_id == self.pk:
                            self.title_cache = obj
                if not self.title_cache and fallback:
                    for rev in revs:
                        obj = rev.object
                        if obj.__class__ == Title:
                            if obj.page_id == self.pk:
                                self.title_cache = obj
            else:
                self.title_cache = Title.objects.get_title(self, language, language_fallback=fallback)
                
                
                
    def get_template(self):
        """
        get the template of this page.
        """
        return self.template

    def get_template_name(self):
        """
        get the template of this page if defined or if closer parent if
        defined or DEFAULT_PAGE_TEMPLATE otherwise
        """
        template = None
        if self.template:
            template = self.template
        if not template:
            for p in self.get_ancestors(ascending=True):
                if p.template:
                    template =  p.template
                    break
        if not template:
            template = settings.CMS_TEMPLATES[0][0]
        for t in settings.CMS_TEMPLATES:
            if t[0] == template:
                return t[1] 
        return _("default")

    #def traductions(self):
    #    langs = ""
    #    for lang in self.get_languages():
    #        langs += '%s, ' % lang
    #    return langs[0:-2]

    def has_page_permission(self, request):
        return self.has_generic_permission(request, "edit")

    def has_publish_permission(self, request):
        return self.has_generic_permission(request, "publish")
    
    def has_softroot_permission(self, request):
        return self.has_generic_permission(request, "softroot")
    
    def has_generic_permission(self, request, type):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if not request.user.is_authenticated() or not request.user.is_staff:
            return False
        if request.user.is_superuser:
            return True
        if not settings.CMS_PERMISSION:
            return True
        else:
            att_name = "permission_%s_cache" % type
            if not hasattr(self, "permission_user_cache") or not hasattr(self, att_name) or request.user.pk != self.permission_user_cache.pk:
                func = getattr(PagePermission.objects, "get_%s_id_list" % type)
                permission = func(request.user)
                self.permission_user_cache = request.user
                if permission == "All" or self.id in permission:
                    setattr(self, att_name, True)
                    self.permission_edit_cache = True
                else:
                    setattr(self, att_name, False)
            return getattr(self, att_name)
    
    def is_home(self):
        if self.parent_id:
            return False
        else:
            return Page.objects.filter(parent=None).order_by('tree_id', 'lft')[0].pk == self.pk
            
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

# Don't register the Page model twice.
try:
    mptt.register(Page)
except mptt.AlreadyRegistered:
    pass

class PagePermission(models.Model):
    """
    Page permission object
    """

    ALLPAGES = 0
    THISPAGE = 1
    PAGECHILDREN = 2

    TYPES = (
        (ALLPAGES, _('All pages')),
        (THISPAGE, _('This page only')),
        (PAGECHILDREN, _('This page and all childrens')),
    )

    type = models.IntegerField(_("type"), choices=TYPES, default=0)
    page = models.ForeignKey(Page, null=True, blank=True, verbose_name=_("page"))
    user = models.ForeignKey(User, verbose_name=_("user"), blank=True, null=True)
    group = models.ForeignKey(Group, verbose_name=_("group"), blank=True, null=True)
    everybody = models.BooleanField(_("everybody"), default=False)
    can_edit = models.BooleanField(_("can edit"), default=True)
    can_change_softroot = models.BooleanField(_("can change soft-root"), default=False)
    can_publish = models.BooleanField(_("can publish"), default=True)
    #can_change_innavigation = models.BooleanField(_("can change in-navigation"), default=True)


    objects = PagePermissionManager()

    def __unicode__(self):
        return "%s :: %s" % (self.user, unicode(PagePermission.TYPES[self.type][1]))

    class Meta:
        verbose_name = _('Page Permission')
        verbose_name_plural = _('Page Permissions')
            
class Title(models.Model):
    language = models.CharField(_("language"), max_length=5, db_index=True)
    title = models.CharField(_("title"), max_length=255)
    menu_title = models.CharField(_("title"), max_length=255, blank=True, null=True, help_text=_("overwrite the title in the menu"))
    slug = models.SlugField(_("slug"), max_length=255, db_index=True, unique=False)
    path = models.CharField(_("path"), max_length=255, db_index=True)
    has_url_overwrite = models.BooleanField(_("has url overwrite"), default=False, db_index=True, editable=False)
    application_urls = models.CharField(_('application'), max_length=200, choices=settings.CMS_APPLICATIONS_URLS, blank=True, null=True, db_index=True)
    redirect = models.CharField(_("redirect"), max_length=255, blank=True, null=True)
    meta_description = models.TextField(_("description"), max_length=255, blank=True, null=True)
    meta_keywords = models.CharField(_("keywords"), max_length=255, blank=True, null=True)
    page_title = models.CharField(_("title"), max_length=255, blank=True, null=True, help_text=_("overwrite the title (html title tag)"))
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    objects = TitleManager()
    
    class Meta:
        unique_together = ('language', 'page')
    
    def __unicode__(self):
        return "%s (%s)" % (self.title, self.slug) 

    def save(self):
        # Build path from parent page's path and slug
        current_path = self.path
        parent_page = self.page.parent
        slug = u'%s' % self.slug
        if parent_page:
            self.path = u'%s/%s' % (Title.objects.get_title(parent_page, language=self.language, language_fallback=True).path, slug)
        else:
            self.path = u'%s' % slug
        super(Title, self).save()
        # Update descendants only if path changed
        if current_path != self.path:
            descendant_titles = Title.objects.filter(
                page__lft__gt=self.page.lft, 
                page__rght__lt=self.page.rght, 
                page__tree_id__exact=self.page.tree_id,
                language=self.language
            )
            for descendant_title in descendant_titles:
                descendant_title.path = descendant_title.path.replace(current_path, self.path, 1)
                descendant_title.save()

    @property
    def overwrite_url(self):
        """Return overrwriten url, or None
        """
        if self.has_url_overwrite:
            return self.path
        return None
        
class EmptyTitle(object):
    """Empty title object, can be returned from Page.get_title_obj() if required
    title object doesn't exists.
    """
    title = ""
    slug = ""
    path = ""
    meta_description = ""
    meta_keywords = ""
    redirect = ""
    has_url_overwite = False
    application_urls = ""
    menu_title = ""
    page_title = ""
    
    @property
    def overwrite_url(self):
        return None
    
class CMSPlugin(models.Model):
    page = models.ForeignKey(Page, verbose_name=_("page"), editable=False)
    parent = models.ForeignKey('self', blank=True, null=True, editable=False)
    position = models.PositiveSmallIntegerField(_("position"), blank=True, null=True, editable=False)
    placeholder = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    language = models.CharField(_("language"), max_length=5, blank=False, db_index=True, editable=False)
    plugin_type = models.CharField(_("plugin_name"), max_length=50, db_index=True, editable=False)
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    def __unicode__(self):
        return ""
    
    def get_plugin_name(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_plugin(self.plugin_type).name
    
    def get_short_description(self):
        return self.get_plugin_instance()[0].__unicode__()        
    
    def get_plugin_class(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_plugin(self.plugin_type)
        
    def get_plugin_instance(self, admin=None):
        from cms.plugin_pool import plugin_pool
        plugin_class = plugin_pool.get_plugin(self.plugin_type)
        plugin = plugin_class(plugin_class.model, admin)# needed so we have the same signature as the original ModelAdmin
        if plugin.model != CMSPlugin and self.__class__ == CMSPlugin:
            # (if self is actually a subclass, getattr below would break)
            try:
                instance = getattr(self, plugin.model.__name__.lower())
                # could alternatively be achieved with:
                # instance = plugin_class.model.objects.get(cmsplugin_ptr=self)
            except:
                instance = None
        else:
            instance = self
        return instance, plugin
    
    def render_plugin(self, context=None, placeholder=None):
        instance, plugin = self.get_plugin_instance()
        if context is None:
            context = Context()
        if instance:
            context = plugin.render(context, instance, placeholder)
            template = hasattr(instance, 'render_template') and instance.render_template or plugin.render_template
            if not template:
                raise ValidationError("plugin has no render_template: %s" % plugin.__class__)
            return mark_safe(render_to_string(template, context))
        else:
            return ""
            
    def get_media_path(self, filename):
        if self.page_id:
            return self.page.get_media_path(filename)
        else: # django 1.0.2 compatibility
            today = date.today()
            return join(settings.CMS_PAGE_MEDIA_PATH, str(today.year), str(today.month), str(today.day), filename)
            
    
    def get_instance_icon_src(self):
        """
        Get src URL for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        if instance:
            return plugin.icon_src(instance)
        else:
            return u''

    def get_instance_icon_alt(self):
        """
        Get alt text for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        if instance:
            return unicode(plugin.icon_alt(instance))
        else:
            return u''
        
    
        
try:
    mptt.register(CMSPlugin)
except mptt.AlreadyRegistered:
    pass

if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(Page, follow=["title_set", "cmsplugin_set", "text", "picture"])
    reversion.register(CMSPlugin)
    reversion.register(Title)
    

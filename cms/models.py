from datetime import datetime
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404

import mptt
from cms import settings
from cms.managers import PageManager, PagePermissionManager, TitleManager

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
    author = models.ForeignKey(User, verbose_name=_("author"))
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', editable=False, db_index=True)
    creation_date = models.DateTimeField(editable=False, default=datetime.now)
    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_('When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True, help_text=_('When to expire the page. Leave empty to never expire.'), db_index=True)
    login_required = models.BooleanField(_('login required'), default=False)
    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(_("soft root"), db_index=True, default=False, help_text=_("All ancestors will not be displayed in the navigation"))
    has_url_overwrite = models.BooleanField(_("has url overwrite"), default=False, db_index=True)
    url_overwrite = models.CharField(_("url overwrite"), max_length=80, db_index=True, blank=True, null=True, help_text=_("The url that this page has instead. Starts with a \"/\""))
    reverse_id = models.CharField(_("reverse url id"), max_length=40, db_index=True, unique=True, blank=True, null=True, help_text=_("An unique identifier that is used with the page_url templatetag for linking to this page"))
    navigation_extenders = models.CharField(_("navigation extenders"), max_length=80, db_index=True, blank=True, null=True, choices=settings.CMS_NAVIGATION_EXTENDERS)
    status = models.IntegerField(_("status"), choices=STATUSES, default=DRAFT, db_index=True)
    template = models.CharField(_("template"), max_length=100, null=True, blank=True, choices=settings.CMS_TEMPLATES, help_text=_('The template used to render the content.'))
    sites = models.ManyToManyField(Site, default=[settings.SITE_ID], help_text=_('The site(s) the page is accessible at.'), verbose_name=_("sites"))
    # Managers
    objects = PageManager()

    #if tagging:
    #    tags = TagField()
        
    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        ordering = ('tree_id', 'lft')
        
    def __unicode__(self):
        #title = u""
        #for t in range(self.level):
        #    title += "+ "
        #title += 
        return self.get_slug()

    def save(self, no_signals=False):
        if not self.status:
            self.status = self.DRAFT
        # Published pages should always have a publication date
        if self.publication_date is None and self.status == self.PUBLISHED:
            self.publication_date = datetime.now()
        # Drafts should not, unless they have been set to the future
        if self.status == self.DRAFT:
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

    def get_absolute_url(self, language=None):
        return reverse('pages-root') + self.get_url(language)

    def get_url(self, language=None):
        """
        get the url of this page, adding parent's slug
        """
        if settings.CMS_UNIQUE_SLUG_REQUIRED:
            url = u'%s/' % self.get_slug(language)
        else:
            url = u'%s-%d/' % (self.get_slug(language), self.id)
        ancestors = self.get_cached_ancestors(ascending=True)
        if ancestors:
            return ancestors[-1].get_url(language) + url
        return url
    
    def get_cached_ancestors(self, ascending=True):
        if ascending:
            if not hasattr(self, "ancestors_ascending"):
                self.ancestors_ascending = list(self.get_ancestors(ascending)) 
            return self.ancestors_ascending
        else:
            if not hasattr(self, "ancestors_descending"):
                self.ancestors_descending = list(self.get_ancestors(ascending))
            return self.ancestors_descending
        
    def get_slug(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the slug of the page depending on the given language
        """
        if not language:
            language = settings.CMS_DEFAULT_LANGUAGE
        if not hasattr(self, "title_cache") or force_reload:
            print "no slug"
            #print self.pk
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
        title = self.title_cache
        if title:
            return title.slug
        else:
            return ""

    def get_title(self, language=None, fallback=True, version_id=None, force_reload=False):
        """
        get the title of the page depending on the given language
        """
        if not language:
            language = settings.CMS_DEFAULT_LANGUAGE
        if not hasattr(self, "title_cache") or force_reload:
            print "no title"
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
        title = self.title_cache
        if title:
            return title.title
        else:
            return None

    def get_template(self):
        """
        get the template of this page if defined or if closer parent if
        defined or DEFAULT_PAGE_TEMPLATE otherwise
        """
        if self.template:
            return self.template
        for p in self.get_ancestors(ascending=True):
            if p.template:
                return p.template
        return settings.DEFAULT_CMS_TEMPLATE

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
            template = settings.DEFAULT_CMS_TEMPLATE
        for t in settings.CMS_TEMPLATES:
            if t[0] == template:
                return t[1] 
        return _("default")

    def traductions(self):
        langs = ""
        for lang in self.get_languages():
            langs += '%s, ' % lang
        return langs[0:-2]

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
        if not self.parent_id and Page.objects.filter(parent=None).order_by('tree_id', 'lft')[0].pk == self.pk:
            return True
        else:
            return False

# Don't register the Page model twice.
try:
    mptt.register(Page)
except mptt.AlreadyRegistered:
    pass

if settings.CMS_PERMISSION:
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
    language = models.CharField(_("language"), max_length=3, db_index=True)
    title = models.CharField(_("title"), max_length=255)
    slug = models.SlugField(_("slug"), max_length=255, db_index=True, unique=False)
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    objects = TitleManager()
    
    def __unicode__(self):
        return "%s (%s)" % (self.title, self.slug) 
    class Meta:
        unique_together = ('language', 'page')
            
class Placeholder(models.Model):
    page = models.ForeignKey(Page, verbose_name=_("page"), editable=False)
    name = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    language = models.CharField(_("language"), max_length=3, blank=False, db_index=True, editable=False)
    body = models.TextField()
    
class CMSPlugin(models.Model):
    page = models.ForeignKey(Page, verbose_name=_("page"), editable=False)
    position = models.PositiveSmallIntegerField(_("position"), default=0, editable=False)
    placeholder = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    language = models.CharField(_("language"), max_length=3, blank=False, db_index=True, editable=False)
    plugin_type = models.CharField(_("plugin_name"), max_length=25, db_index=True, editable=False)
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    def get_plugin_name(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_plugin(self.plugin_type).name
    
    def get_plugin_instance(self):
        from cms.plugin_pool import plugin_pool
        plugin = plugin_pool.get_plugin(self.plugin_type)()
        try:
            instance = getattr(self, plugin.model.__name__.lower())
        except:
            instance = None
        return instance, plugin
    
    def render(self, request):
        instance, plugin = self.get_plugin_instance()
        if instance:
            return plugin.render(request, instance)
        else:
            return ""
        
    #class Meta:
    #    pass
        #abstract = True

if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(Page, follow=["title_set", "cmsplugin_set", "text", "picture"])
    reversion.register(CMSPlugin)
    reversion.register(Title)
    
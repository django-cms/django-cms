from datetime import datetime

from django.db import models
from django.contrib.auth.models import User, Group
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.core.exceptions import ImproperlyConfigured
from django.contrib.sites.models import Site


import mptt
from cms import settings
from cms.managers import PageManager, ContentManager, PagePermissionManager,\
    TitleManager

try:
    tagging = models.get_app('tagging')
    from tagging.fields import TagField
except ImproperlyConfigured:
    tagging = False

if not settings.CMS_TAGGING:
    tagging = False

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
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    creation_date = models.DateTimeField(editable=False, default=datetime.now)
    publication_date = models.DateTimeField(_("publication date"), null=True, blank=True, help_text=_('When the page should go live. Status must be "Published" for page to go live.'), db_index=True)
    publication_end_date = models.DateTimeField(_("publication end date"), null=True, blank=True, help_text=_('When to expire the page. Leave empty to never expire.'), db_index=True)
    login_required = models.BooleanField(_('login required'), default=False)
    in_navigation = models.BooleanField(_("in navigation"), default=True)
    soft_root = models.BooleanField(_("soft root"), default=False, help_text=_("All subpages will not be displayed in the navigation"))
    status = models.IntegerField(_("status"), choices=STATUSES, default=DRAFT)
    template = models.CharField(_("template"), max_length=100, null=True, blank=True)
    sites = models.ManyToManyField(Site, default=[settings.SITE_ID], help_text=_('The site(s) the page is accessible at.'), verbose_name=_("sites"))
    # Managers
    objects = PageManager()

    if tagging:
        tags = TagField()
        
    class Meta:
        verbose_name = _('page')
        verbose_name_plural = _('pages')
        
    def __unicode__(self):
        return self.get_slug()

    def save(self):
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
        languages = []
        for t in titles:
            if t.language not in languages:
                languages.append(t.language)
        return languages

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
        for ancestor in self.get_ancestors(ascending=True):
            url = ancestor.get_slug(language) + u'/' + url
        return url

    def get_slug(self, language=None, fallback=True):
        """
        get the slug of the page depending on the given language
        """
        if not language:
            language = settings.CMS_DEFAULT_LANGUAGE
        if not hasattr(self, "title_cache"):
            #print "no slug"
            
            self.title_cache = Title.objects.get_title(self, language, language_fallback=fallback)
        title = self.title_cache
        if title:
            return title.slug
        else:
            return ""

    def get_title(self, language=None, fallback=True):
        """
        get the title of the page depending on the given language
        """
        if not language:
            language = settings.CMS_DEFAULT_LANGUAGE
        if not hasattr(self, "title_cache"):
            #print "no title"
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

    def traductions(self):
        langs = ""
        for lang in self.get_languages():
            langs += '%s, ' % lang
        return langs[0:-2]

    def has_page_permission(self, request):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if not settings.CMS_PERMISSION:
            return True
        else:
            permission = PagePermission.objects.get_page_id_list(request.user)
            if permission == "All":
                return True
            if self.id in permission:
                return True
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
        TYPES = (
            (0, _('All')),
            (1, _('This page only')),
            (2, _('This page and all childrens')),
        )
        
        page = models.ForeignKey(Page, null=True, blank=True, verbose_name=_("page"))
        
        user = models.ForeignKey(User, verbose_name=_("user"), blank=True, null=True)
        group = models.ForeignKey(Group, verbose_name=_("group"), blank=True, null=True)
        
        can_create_pages = models.BooleanField(default=True)
        can_edit_other_author_pages = models.BooleanField(default=True)
        can_delete_pages = models.BooleanField(default=True)
        can_publish = models.BooleanField(default=True)
        can_change_softroot = models.BooleanField(default=False)
        can_change_innavigation = models.BooleanField(default=True)
        
        type = models.IntegerField(_("type"), choices=TYPES, default=0)
        
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
        pass
        #unique_together = ('language', 'page')

class CMSPlugin(models.Model):
    page = models.ForeignKey(Page, verbose_name=_("page"))
    position = models.PositiveSmallIntegerField(default=0)
    slot = models.CharField(max_length=50, default=0)
    language = models.CharField(_("language"), max_length=3, blank=False, db_index=True)
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    class Meta:
        abstract = True
    
class Content(CMSPlugin):
    """A block of content, tied to a page, for a particular language"""
    body = models.TextField(_("body"))
    type = models.CharField(_("type"), max_length=100, blank=False)
    
    objects = ContentManager()

    def __unicode__(self):
        return "%s :: %s" % (self.page.get_slug(), self.body[0:15])

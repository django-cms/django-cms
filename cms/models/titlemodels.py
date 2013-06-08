# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from cms.models.managers import TitleManager
from cms.models.pagemodel import Page
from cms.utils.helpers import reversion_register


class Title(models.Model):
    language = models.CharField(_("language"), max_length=15, db_index=True)
    title = models.CharField(_("title"), max_length=255)
    page_title = models.CharField(_("title"), max_length=255, blank=True, null=True,
                                  help_text=_("overwrite the title (html title tag)"))
    menu_title = models.CharField(_("title"), max_length=255, blank=True, null=True,
                                  help_text=_("overwrite the title in the menu"))
    meta_description = models.TextField(_("description"), max_length=155, blank=True, null=True,
                                        help_text=_("The text displayed in search engines."))
    slug = models.SlugField(_("slug"), max_length=255, db_index=True, unique=False)
    path = models.CharField(_("Path"), max_length=255, db_index=True)
    has_url_overwrite = models.BooleanField(_("has url overwrite"), default=False, db_index=True, editable=False)
    application_urls = models.CharField(_('application'), max_length=200, blank=True, null=True, db_index=True)
    redirect = models.CharField(_("redirect"), max_length=255, blank=True, null=True)
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=timezone.now)
    objects = TitleManager()

    class Meta:
        unique_together = (('language', 'page'), )
        app_label = 'cms'

    def __unicode__(self):
        return u"%s (%s, %s)" % (self.title, self.slug, self.language)

    def update_path(self):
        # Build path from parent page's path and slug
        slug = u'%s' % self.slug
        if not self.has_url_overwrite:
            self.path = u'%s' % slug
            if self.page.parent_id:
                parent_page = self.page.parent_id

                parent_title = Title.objects.get_title(parent_page, language=self.language, language_fallback=True)
                if parent_title:
                    self.path = u'%s/%s' % (parent_title.path, slug)

    @property
    def overwrite_url(self):
        """Return overwritten url, or None
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
    redirect = ""
    has_url_overwrite = False
    application_urls = ""
    menu_title = ""
    page_title = ""

    @property
    def overwrite_url(self):
        return None

reversion_register(Title)

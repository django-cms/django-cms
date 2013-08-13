# -*- coding: utf-8 -*-
from cms.utils.compat.dj import python_2_unicode_compatible
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from cms.models.managers import TitleManager
from cms.models.pagemodel import Page
from cms.utils.helpers import reversion_register


@python_2_unicode_compatible
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
    redirect = models.CharField(_("redirect"), max_length=255, blank=True, null=True)
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=timezone.now)

     # Publisher fields
    publisher_is_draft = models.BooleanField(default=True, editable=False, db_index=True)
    # This is misnamed - the one-to-one relation is populated on both ends
    publisher_public = models.OneToOneField('self', related_name='publisher_draft', null=True, editable=False)
    publisher_state = models.SmallIntegerField(default=0, editable=False, db_index=True)
    # If the draft is loaded from a reversion version save the revision id here.
    revision_id = models.PositiveIntegerField(default=0, editable=False)
    objects = TitleManager()

    class Meta:
        unique_together = (('language', 'page'),)
        app_label = 'cms'

    def __str__(self):
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

    def is_dirty(self):
        return self.publisher_state == self.PUBLISHER_STATE_DIRTY


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

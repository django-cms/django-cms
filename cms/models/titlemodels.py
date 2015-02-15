# -*- coding: utf-8 -*-
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from cms.constants import PUBLISHER_STATE_DIRTY
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
    redirect = models.CharField(_("redirect"), max_length=2048, blank=True, null=True)
    page = models.ForeignKey(Page, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=timezone.now)

    # Publisher fields
    published = models.BooleanField(_("is published"), blank=True, default=False)
    publisher_is_draft = models.BooleanField(default=True, editable=False, db_index=True)
    # This is misnamed - the one-to-one relation is populated on both ends
    publisher_public = models.OneToOneField('self', related_name='publisher_draft', null=True, editable=False)
    publisher_state = models.SmallIntegerField(default=0, editable=False, db_index=True)

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
        return self.publisher_state == PUBLISHER_STATE_DIRTY

    def save_base(self, *args, **kwargs):
        """Overridden save_base. If an instance is draft, and was changed, mark
        it as dirty.

        Dirty flag is used for changed nodes identification when publish method
        takes place. After current changes are published, state is set back to
        PUBLISHER_STATE_DEFAULT (in publish method).
        """
        keep_state = getattr(self, '_publisher_keep_state', None)

        # Published pages should always have a publication date
        # if the page is published we set the publish date if not set yet.
        if self.page.publication_date is None and self.published:
            self.page.publication_date = timezone.now() - timedelta(seconds=5)

        if self.publisher_is_draft and not keep_state and self.is_new_dirty():
            self.publisher_state = PUBLISHER_STATE_DIRTY
        if keep_state:
            delattr(self, '_publisher_keep_state')
        ret = super(Title, self).save_base(*args, **kwargs)
        return ret

    def is_new_dirty(self):
        if self.pk:
            fields = [
                'title', 'page_title', 'menu_title', 'meta_description', 'slug', 'has_url_overwrite', 'redirect'
            ]
            try:
                old_title = Title.objects.get(pk=self.pk)
            except Title.DoesNotExist:
                return True
            for field in fields:
                old_val = getattr(old_title, field)
                new_val = getattr(self, field)
                if not old_val == new_val:
                    return True
            return False
        return True


class EmptyTitle(object):

    def __init__(self, language):
        self.language = language

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
    published = False

    @property
    def overwrite_url(self):
        return None


def _reversion():
    exclude_fields = ['publisher_is_draft', 'publisher_public', 'publisher_state']

    reversion_register(
        Title,
        exclude_fields=exclude_fields
    )


_reversion()
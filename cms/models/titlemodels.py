# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from cms.constants import PUBLISHER_STATE_DIRTY
from cms.models.managers import TitleManager
from cms.models.pagemodel import Page

from six import python_2_unicode_compatible


@python_2_unicode_compatible
class Title(models.Model):
    # These are the fields whose values are compared when saving
    # a Title object to know if it has changed.
    editable_fields = [
        'title',
        'slug',
        'redirect',
        'page_title',
        'menu_title',
        'meta_description',
        'has_url_overwrite',
    ]

    language = models.CharField(_("language"), max_length=15, db_index=True)
    title = models.CharField(_("title"), max_length=255)
    page_title = models.CharField(_("title"), max_length=255, blank=True, null=True,
                                  help_text=_("overwrite the title (html title tag)"))
    menu_title = models.CharField(_("title"), max_length=255, blank=True, null=True,
                                  help_text=_("overwrite the title in the menu"))
    meta_description = models.TextField(_("description"), blank=True, null=True,
                                        help_text=_("The text displayed in search engines."))
    slug = models.SlugField(_("slug"), max_length=255, db_index=True, unique=False)
    path = models.CharField(_("Path"), max_length=255, db_index=True)
    has_url_overwrite = models.BooleanField(_("has url overwrite"), default=False, db_index=True, editable=False)
    redirect = models.CharField(_("redirect"), max_length=2048, blank=True, null=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, verbose_name=_("page"), related_name="title_set")
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=timezone.now)

    # Publisher fields
    published = models.BooleanField(_("is published"), blank=True, default=False)
    publisher_is_draft = models.BooleanField(default=True, editable=False, db_index=True)
    # This is misnamed - the one-to-one relation is populated on both ends
    publisher_public = models.OneToOneField(
        'self',
        on_delete=models.CASCADE,
        related_name='publisher_draft',
        null=True,
        editable=False,
    )
    publisher_state = models.SmallIntegerField(default=0, editable=False, db_index=True)

    objects = TitleManager()

    class Meta:
        unique_together = (('language', 'page'),)
        app_label = 'cms'

    def __str__(self):
        return u"%s (%s, %s)" % (self.title, self.slug, self.language)

    def __repr__(self):
        display = '<{module}.{class_name} id={id} is_draft={is_draft} object at {location}>'.format(
            module=self.__module__,
            class_name=self.__class__.__name__,
            id=self.pk,
            is_draft=self.publisher_is_draft,
            location=hex(id(self)),
        )
        return display

    def get_path_for_base(self, base_path=''):
        old_base, sep, slug = self.path.rpartition('/')
        return '%s/%s' % (base_path, slug) if base_path else slug

    @property
    def has_path_override(self):
        return self.has_url_overwrite or bool(self.redirect)

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

        if self.publisher_is_draft and not keep_state and self.is_new_dirty():
            self.publisher_state = PUBLISHER_STATE_DIRTY

        if keep_state:
            delattr(self, '_publisher_keep_state')
        return super(Title, self).save_base(*args, **kwargs)

    def is_new_dirty(self):
        if not self.pk:
            return True

        try:
            old_title = Title.objects.get(pk=self.pk)
        except Title.DoesNotExist:
            return True

        for field in self.editable_fields:
            old_val = getattr(old_title, field)
            new_val = getattr(self, field)
            if not old_val == new_val:
                return True

        if old_title.path != self.path and self.has_url_overwrite:
            # path is handled individually because its a special field.
            # The path field is both an internal and user facing field,
            # as such we can't mark the title as dirty on any change,
            # instead we need to check if the url overwrite flag is set.
            return True
        return False

    def _url_properties_changed(self):
        assert self.publisher_is_draft
        assert self.publisher_public_id

        new_values = (
            self.path,
            self.slug,
            self.published,
        )
        old_values = (
            self.publisher_public.path,
            self.publisher_public.slug,
            self.publisher_public.published,
        )
        return old_values != new_values


class EmptyTitle(object):
    """
    Empty title object, can be returned from Page.get_title_obj() if required
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

    def __init__(self, language):
        self.language = language

    def __nonzero__(self):
        # Python 2 compatibility
        return False

    def __bool__(self):
        # Python 3 compatibility
        return False

    @property
    def overwrite_url(self):
        return None

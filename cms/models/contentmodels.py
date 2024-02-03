from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from cms import constants
from cms.models.fields import PlaceholderRelationField
from cms.models.managers import ContentAdminManager, PageContentManager
from cms.models.pagemodel import Page
from cms.utils.conf import get_cms_setting


class PageContent(models.Model):
    LIMIT_VISIBILITY_IN_MENU_CHOICES = (
        (constants.VISIBILITY_ALL, _('no limit set')),
        (constants.VISIBILITY_USERS, _('for logged in users only')),
        (constants.VISIBILITY_ANONYMOUS, _('for anonymous users only')),
    )
    TEMPLATE_DEFAULT = constants.TEMPLATE_INHERITANCE_MAGIC if get_cms_setting(
        'TEMPLATE_INHERITANCE') else get_cms_setting('TEMPLATES')[0][0]

    X_FRAME_OPTIONS_CHOICES = (
        (constants.X_FRAME_OPTIONS_INHERIT, _('Inherit from parent page')),
        (constants.X_FRAME_OPTIONS_DENY, _('Deny')),
        (constants.X_FRAME_OPTIONS_SAMEORIGIN, _('Only this website')),
        (constants.X_FRAME_OPTIONS_ALLOW, _('Allow'))
    )

    template_choices = [(x, _(y)) for x, y in get_cms_setting('TEMPLATES')]

    # These are the fields whose values are compared when saving
    # a PageContent object to know if it has changed.
    editable_fields = [
        'title',
        'redirect',
        'page_title',
        'menu_title',
        'meta_description',
    ]

    language = models.CharField(_("language"), max_length=15, db_index=True)
    title = models.CharField(_("title"), max_length=255)
    page_title = models.CharField(
        _("title"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("overwrite the title (html title tag)")
    )
    menu_title = models.CharField(
        _("title"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("overwrite the title in the menu")
    )
    meta_description = models.TextField(
        _("description"),
        blank=True,
        null=True,
        help_text=_("The text displayed in search engines.")
    )
    redirect = models.CharField(
        _("redirect"),
        max_length=2048,
        blank=True,
        null=True
    )
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        verbose_name=_("page"),
        related_name="pagecontent_set"
    )
    creation_date = models.DateTimeField(
        _("creation date"),
        editable=False,
        default=timezone.now
    )
    # Placeholders (plugins)
    placeholders = PlaceholderRelationField()

    created_by = models.CharField(
        _("created by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    changed_by = models.CharField(
        _("changed by"), max_length=constants.PAGE_USERNAME_MAX_LENGTH,
        editable=False)
    changed_date = models.DateTimeField(auto_now=True)

    in_navigation = models.BooleanField(_("in navigation"), default=True, db_index=True)
    soft_root = models.BooleanField(
        _("soft root"),
        db_index=True,
        default=False,
        help_text=_("All ancestors will not be displayed in the navigation")
    )
    template = models.CharField(
        _("template"),
        max_length=100,
        choices=template_choices,
        help_text=_('The template used to render the content.'),
        default=TEMPLATE_DEFAULT
    )
    limit_visibility_in_menu = models.SmallIntegerField(
        _("menu visibility"),
        default=constants.VISIBILITY_ALL,
        choices=LIMIT_VISIBILITY_IN_MENU_CHOICES,
        db_index=True,
        blank=True,
        null=True,
        help_text=_("limit when this page is visible in the menu")
    )

    # X Frame Options for clickjacking protection
    xframe_options = models.IntegerField(
        choices=X_FRAME_OPTIONS_CHOICES,
        default=get_cms_setting('DEFAULT_X_FRAME_OPTIONS'),
    )

    objects = PageContentManager()
    admin_manager = ContentAdminManager()
    """Admin_manager does lack additional functionality of objects and must only
    be used inside admin objects or admin forms. One of its key properties is that
    it can access all objects of type PageContent (irrespevtively of some objects
    being hidden by third-party packages, e.g. due to viewing rights, publication
    or moderation status.
    """

    class Meta:
        verbose_name = _("page content")
        verbose_name_plural = _("page contents")
        default_permissions = []
        unique_together = (('language', 'page'),)
        app_label = 'cms'

    def __str__(self):
        return "%s (%s)" % (self.title, self.language)

    def __repr__(self):
        display = f'<{self.__module__}.{self.__class__.__name__} id={self.pk} object at {hex(id(self))}>'
        return display

    def update(self, **data):
        for field, value in data.items():
            setattr(self, field, value)
        self.save(update_fields=data.keys())

    def save(self, **kwargs):
        # delete template cache
        if hasattr(self, '_template_cache'):
            delattr(self, '_template_cache')
        super().save(**kwargs)

    def toggle_in_navigation(self, set_to=None):
        '''
        Toggles (or sets) in_navigation and invalidates the cms page cache
        '''
        old = bool(self.in_navigation)

        if set_to in [True, False]:
            new = set_to
        else:
            new = not old

        self.update(in_navigation=new)

        # If there was a change, invalidate the cms page cache
        if new != old:
            self.page.clear_cache()
        return new

    def has_placeholder_change_permission(self, user):
        return self.page.has_change_permission(user)

    def rescan_placeholders(self):
        """
        Rescan and if necessary create placeholders in the current template.
        """
        from cms.utils.placeholder import rescan_placeholders_for_obj

        return rescan_placeholders_for_obj(self)

    def get_placeholders(self):
        if not hasattr(self, '_placeholder_cache'):
            self._placeholder_cache = self.placeholders.all()
        return self._placeholder_cache

    def get_ancestor_titles(self):
        return PageContent.objects.filter(
            page__in=self.page.get_ancestor_pages(),
            language=self.language,
        )

    def get_template(self):
        """
        get the template of this page if defined or if closer parent if
        defined or DEFAULT_PAGE_TEMPLATE otherwise
        """
        if hasattr(self, '_template_cache'):
            return self._template_cache

        if self.template != constants.TEMPLATE_INHERITANCE_MAGIC:
            self._template_cache = self.template or get_cms_setting('TEMPLATES')[0][0]
            return self._template_cache

        templates = (
            self
            .get_ancestor_titles()
            .exclude(template=constants.TEMPLATE_INHERITANCE_MAGIC)
            .order_by('-page__node__path')
            .values_list('template', flat=True)
        )

        try:
            self._template_cache = templates[0]
        except IndexError:
            self._template_cache = get_cms_setting('TEMPLATES')[0][0]
        return self._template_cache

    def get_template_name(self):
        """
        get the textual name (2nd parameter in get_cms_setting('TEMPLATES'))
        of the template of this title. failing to find that, return the
        name of the default template.
        """
        template = self.get_template()
        for t in get_cms_setting('TEMPLATES'):
            if t[0] == template:
                return t[1]
        return _("default")

    def is_editable(self, request):
        """returns True if page content object itself can be edited. Does not check
        user permissions to do that.

        :rtype: ``bool``
        """
        return True

    def content_indicator(self):
        """returns the content indicator status. Without additional packages like
        djangocms-versioning page content always is public.

        :rtype: ``str``
        """
        return "public" if self.get_absolute_url(language=self.language) else "unpublished-parent"

    def get_xframe_options(self):
        """ Finds X_FRAME_OPTION from tree if inherited """
        xframe_options = self.xframe_options or constants.X_FRAME_OPTIONS_INHERIT

        if xframe_options != constants.X_FRAME_OPTIONS_INHERIT:
            return xframe_options

        # Ignore those pages which just inherit their value
        ancestors = self.get_ancestor_titles().order_by('-page__node__path')
        ancestors = ancestors.exclude(xframe_options=constants.X_FRAME_OPTIONS_INHERIT)

        # Now just give me the clickjacking setting (not anything else)
        xframe_options = ancestors.values_list('xframe_options', flat=True)

        try:
            return xframe_options[0]
        except IndexError:
            return None

    def get_absolute_url(self, language=None):
        """Get the absolute url for the page content. If language is specified it will return
        the absolute url of the corresponding "sister" content."""
        return self.page.get_absolute_url(language=language or self.language)


class EmptyPageContent:
    """
    Empty title object, can be returned from :meth:`cms.models.pagemodel.Page.get_content_obj` if required
    title object doesn't exist.
    """
    title = ""
    meta_description = ""
    redirect = ""
    application_urls = ""
    menu_title = ""
    page_title = ""
    xframe_options = None
    template = get_cms_setting('TEMPLATES')[0][0]
    soft_root = False
    in_navigation = False

    def __init__(self, language, page=None):
        self.language = language
        self.page = page

    def __bool__(self):
        return False

    def content_indicator(self):
        """returns the content indicator status. Empty page content always is empty

        :rtype: ``str``
        """
        return "empty"

    def is_editable(self, request):
        """returns True if empty page content object itself can be edited. Since editing creates a new
        page content object this should always be True

        :rtype: ``bool``
        """
        return True

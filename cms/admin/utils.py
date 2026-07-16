import re
import typing
import warnings
from copy import copy
from functools import partial
from urllib.parse import parse_qsl

from asgiref.local import Local
from django import forms
from django.contrib.admin import ModelAdmin
from django.contrib.admin.checks import ModelAdminChecks
from django.contrib.admin.utils import label_for_field
from django.contrib.admin.views.main import ChangeList
from django.contrib.auth import get_permission_codename
from django.contrib.sites.models import Site
from django.core import checks
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.db.models import DateField, OuterRef, Subquery, functions
from django.db.models.functions import Cast
from django.forms import modelform_factory, modelformset_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, path
from django.utils.decorators import method_decorator
from django.utils.html import format_html, format_html_join
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext_lazy as _
from django.views.decorators.http import require_GET

from cms.models.managers import ContentAdminManager
from cms.toolbar.utils import get_object_edit_url
from cms.utils import get_current_site, get_language_from_request
from cms.utils.compat.warnings import RemovedInDjangoCMS60Warning
from cms.utils.helpers import is_editable_model
from cms.utils.i18n import get_language_dict, get_language_list, get_language_tuple
from cms.utils.urlutils import admin_reverse, static_with_version


class ChangeListActionsMixin(metaclass=forms.widgets.MediaDefiningClass):
    """ChangeListActionsMixin is a mixin for the ModelAdmin class. It adds the ability to have
    action buttons and a burger menu in the admin's change list view. Unlike actions that affect
    multiple listed items the list action buttons only affect one item at a time.

    Use :meth:`~cms.admin.utils.ChangeListActionsMixin.get_action_list` to register actions and
    :meth:`~cms.admin.utils.ChangeListActionsMixin.admin_action_button` to define the button
    behavior.

    To activate the actions make sure ``"admin_list_actions"`` is in the admin classes
    :attr:`~django.contrib.admin.ModelAdmin.list_display` property.
    """

    class Media:
        js = (
            "admin/js/jquery.init.js",
            "cms/js/admin/actions.js",
        )
        css = {"all": (static_with_version("cms/css/cms.admin.css"),)}

    EMPTY_ACTION = mark_safe('<span class="cms-empty-action"></span>')

    def get_actions_list(
        self,
    ) -> list[typing.Callable[[models.Model, HttpRequest], str]]:
        """Collect list actions from implemented methods and return as list. Make sure to call
        it's ``super()`` instance when overwriting::

            class MyModelAdmin(admin.ModelAdmin):
                ...

                def get_actions_list(self):
                    return super().get_actions_list() + [
                        self.my_first_action,
                        self.my_second_action,
                    ]
        """
        return []

    def get_admin_list_actions(self, request: HttpRequest) -> typing.Callable[[models.Model], str]:
        """Method to register the admin action menu with the admin's list display

        Usage (in your model admin)::

            class MyModelAdmin(AdminActionsMixin, admin.ModelAdmin):
                ...
                list_display = ("name", ..., "admin_list_actions")

        """

        def list_actions(obj: models.Model) -> str:
            """The name of this inner function must not change. css styling and js depends on it."""
            return format_html_join(
                "",
                "{}",
                ((action(obj, request),) for action in self.get_actions_list()),
            )

        list_actions.short_description = _("Actions")
        return list_actions

    def admin_list_actions(self, obj: models.Model) -> None:
        raise ValueError(
            'ModelAdmin.display_list contains "admin_list_actions" as a placeholder for list action icons. '
            'ChangeListActionsMixin is not loaded, however. If you implement "get_list_display" make '
            "sure it calls super().get_list_display."
        )  # pragma: no cover

    def get_list_display(self, request: HttpRequest) -> tuple[str | typing.Callable[[models.Model], str], ...]:
        list_display = super().get_list_display(request)
        return tuple(
            self.get_admin_list_actions(request) if item == "admin_list_actions" else item for item in list_display
        )

    @staticmethod
    def admin_action_button(
        url: str,
        icon: str,
        title: str,
        burger_menu: bool = False,
        action: str = "get",
        disabled: bool = False,
        keepsideframe: bool = True,
        name: str = "",
    ) -> str:
        """Returns a generic button supported by the ChangeListActionsMixin.

        :param str url:  Url of the action as string, typically generated by :func:`~cms.utils.urlutils.admin_reverse`_
        :param str icon: Name of the icon shown in the button or before the title in the burger menu.
        :param str title: Human-readable string describing the action.
        :param bool burger_menu: If ``True`` the action item will be part of a burger menu right og all buttons.
        :param str action: Either ``"get"`` or ``"post"`` defining the html method used for the url. Some urls
                           require a post method.
        :param bool disabled: If ``True`` the item is grayed out and cannot be selected.
        :param bool keepsideframe:  If ``False`` the side frame (if open) will be closed before executing the action.
        :param str name: A string that will be added to the class list of the button/menu item:
                         ``cms-action-{{ name }}``

        To add an action button to the change list use the following pattern in your admin class::

                 def my_custom_button(self, obj, request, disabled=False):
                     # do preparations, e.g., check permissions, get url, ...
                     url = admin_reverse("...", args=[obj.pk])
                     if permissions_ok:
                         return self.admin_action_button(
                             url, "info", _("View usage"), disabled=disabled
                         )
                     return ""  # No button

        """
        return render_to_string(
            "admin/cms/icons/base.html",
            {
                "url": url or "",
                "icon": icon,
                "method": action,
                "disabled": disabled,
                "keepsideframe": keepsideframe,
                "title": title,
                "burger_menu": burger_menu,
                "name": name,
            },
        )


#: Prefix for content model fields to be added to the grouper admin and to the change form.
CONTENT_PREFIX = "content__"


class GrouperChangeListBase(ChangeList):
    """Subclass ChangeList to disregard grouping fields get parameter as filter"""

    current_language: str | None = None
    available_languages: tuple[tuple[str, str], ...] = ()
    _extra_grouping_fields: list[str] = []

    def get_filters_params(self, params: dict | None = None):
        lookup_params = super().get_filters_params(params)
        for field in self._extra_grouping_fields:
            if field in lookup_params:
                del lookup_params[field]
        return lookup_params


class GrouperModelAdminChecks(ModelAdminChecks):
    def _check_list_editable_item(self, obj, field_name, label):
        """Check content model fields against the content model."""
        if field_name.startswith(CONTENT_PREFIX) and obj.content_model:
            content_field_name = field_name[len(CONTENT_PREFIX) :]
            if content_field_name == obj.grouper_field_name or content_field_name in obj.extra_grouping_fields:
                return [
                    checks.Error(
                        f"The value of '{label}' refers to '{field_name}', which cannot be edited "
                        "from the changelist.",
                        obj=obj.__class__,
                        id="admin.E125",
                    )
                ]
            content_obj = copy(obj)
            content_obj.model = obj.content_model
            content_obj.list_display = tuple(
                item[len(CONTENT_PREFIX) :] if isinstance(item, str) and item.startswith(CONTENT_PREFIX) else item
                for item in obj.list_display
            )
            if obj.list_display_links:
                content_obj.list_display_links = tuple(
                    item[len(CONTENT_PREFIX) :]
                    if isinstance(item, str) and item.startswith(CONTENT_PREFIX)
                    else item
                    for item in obj.list_display_links
                )
            return super()._check_list_editable_item(content_obj, content_field_name, label)
        return super()._check_list_editable_item(obj, field_name, label)

    def _check_prepopulated_fields_value_item(self, obj, field_name, label):
        """For `prepopulated_fields` equal to {"slug": ("content__title",)},
        `field_name` is "content__title"."""

        if field_name.startswith(CONTENT_PREFIX) and obj.content_model:
            field_name = field_name[len(CONTENT_PREFIX) :]
            obj = copy(obj)
            obj.model = obj.content_model
        return super()._check_prepopulated_fields_value_item(obj, field_name, label)

    def _check_prepopulated_fields_key(self, obj, field_name, label):
        """Check a key of `prepopulated_fields` dictionary, i.e. check that it
        is a name of existing field and the field is one of the allowed types.
        """

        if field_name.startswith(CONTENT_PREFIX) and obj.content_model:
            field_name = field_name[len(CONTENT_PREFIX) :]
            obj = copy(obj)
            obj.model = obj.content_model
        return super()._check_prepopulated_fields_key(obj, field_name, label)


_UNSET = object()


class Grouping:
    """Request-scoped grouping state of a :class:`GrouperModelAdmin`.

    :attr:`filters` maps each of the admin's
    :attr:`~GrouperModelAdmin.extra_grouping_fields` (e.g. ``"language"``) to its
    current value. :attr:`requested_content_obj` holds the content object explicitly
    selected via the :attr:`~GrouperModelAdmin.content_pk_url_param` GET parameter,
    or ``None``. Grouping values are also available as attributes, e.g.
    ``grouping.language``.

    Instances are created per request by
    :meth:`GrouperModelAdmin.get_grouping_from_request` and retrieved with
    :meth:`GrouperModelAdmin.get_grouping`. Do not store them beyond the request
    they were created for.
    """

    def __init__(
        self,
        filters: dict[str, typing.Any] | None = None,
        requested_content_obj: models.Model | None = None,
    ):
        self.filters: dict[str, typing.Any] = dict(filters or {})
        self.requested_content_obj = requested_content_obj

    def __getattr__(self, name: str) -> typing.Any:
        try:
            return self.__dict__["filters"][name]
        except KeyError:
            raise AttributeError(name) from None

    def __repr__(self) -> str:
        return f"Grouping({self.filters!r}, requested_content_obj={self.requested_content_obj!r})"


class _GroupingFieldShim:
    """Backward-compatibility data descriptor for grouping values that historically were
    stored as attributes of the shared ``ModelAdmin`` instance (e.g. ``admin.language``) -
    an unsafe pattern, since concurrent requests overwrote each other's values.

    Reads, writes, and deletes are redirected to the :class:`Grouping` published for the
    current thread/async task, keeping the historic attribute API intact for subclasses
    and third-party packages while making it thread-safe. New code should use
    :meth:`GrouperModelAdmin.get_grouping` instead.
    """

    def __init__(self, field: str, default: typing.Any = _UNSET):
        self.field = field
        self.default = default

    def _deprecation_warning(self) -> None:
        warnings.warn(
            f"Accessing request-dependent grouping values as admin instance attributes "
            f"(self.{self.field}) is deprecated. Use self.get_grouping(request).{self.field} instead.",
            RemovedInDjangoCMS60Warning,
            stacklevel=3,
        )

    def __get__(self, instance, owner=None) -> typing.Any:
        if instance is None:
            return self
        self._deprecation_warning()
        grouping = getattr(instance._local_grouping, "current", None)
        if grouping is not None and self.field in grouping.filters:
            return grouping.filters[self.field]
        if self.default is _UNSET:
            raise AttributeError(self.field)
        return self.default

    def __set__(self, instance, value) -> None:
        self._deprecation_warning()
        grouping = getattr(instance._local_grouping, "current", None)
        if grouping is None:
            grouping = instance._local_grouping.current = Grouping()
        grouping.filters[self.field] = value

    def __delete__(self, instance) -> None:
        self._deprecation_warning()
        grouping = getattr(instance._local_grouping, "current", None)
        if grouping is None or self.field not in grouping.filters:
            raise AttributeError(self.field)
        del grouping.filters[self.field]


class _RequestedContentObjShim:
    """Thread-safe stand-in for the former ``_requested_content_obj`` instance attribute,
    proxying to the :class:`Grouping` published for the current thread/async task."""

    def __get__(self, instance, owner=None) -> models.Model | None:
        if instance is None:
            return self
        grouping = getattr(instance._local_grouping, "current", None)
        return grouping.requested_content_obj if grouping else None

    def __set__(self, instance, value) -> None:
        grouping = getattr(instance._local_grouping, "current", None)
        if grouping is None:
            grouping = instance._local_grouping.current = Grouping()
        grouping.requested_content_obj = value


class GrouperModelAdmin(ChangeListActionsMixin, ModelAdmin):
    """Easy-to-use ModelAdmin for grouper models. Usage example::

        class MyGrouperAdmin(GrouperModelAdmin):
            # Add language tabs to change and add views
            extra_grouping_fields = ("language",)
            # Add grouper and content fields to change list view
            # Add preview and settings action to change list view
            list_display = ("field_in_grouper_model", "content__field_in_content_model", "admin_list_actions")

            # Automatically add content fields to change form (either the standard form or any form given
            form = MyChangeForm

            ...

    Using ``GrouperModelAdmin`` instead of :class:`~django.contrib.admin.ModelAdmin` adds a view standard functions
    to your admin class to make it more easily and more consistently customizable.

    1. By adding ``"admin_list_actions"`` to the admin's :attr:`~django.contrib.admin.ModelAdmin.list_display`
        attribute the change list view gets an action column as described by
        :class:`~cms.admin.utils.ChangeListActionsMixin`.
    2. The admin class automatically creates a method for each field of the content model form (default: all fields)
        named ``content__{content_model_field_name}``. Those fields can be used in
        :attr:`~django.contrib.admin.ModelAdmin.list_display` just as grouper model fields.
        Currently, they are not sortable, however.
    3. The change form is amended with exactly those content fields also named ``content__{content_model_field_name}``.
        As a result, the change form can (but does not have to) contain both grouper model fields and content model
        fields. The admin takes care of creating the necessary model instances.
    """

    #: The name of the ``ForeignKey`` in the content model that points to the grouper instance. If not given
    #: it is assumed to be the snake case name of the grouper model class, e.g. ``"blog_post"`` for the
    #: ``"BlogPost"`` model.
    grouper_field_name: str | None = None
    #: Indicates additional grouping fields such as ``"language"`` for example. Additional grouping fields create
    #: tabs in the change form and a dropdown menu in the change list view.
    #:
    #: .. note::
    #:
    #:      All fields serving as extra grouping fields must be part of the admin's
    #:      :attr:`~django.contrib.admin.ModelAdmin.fieldsets` setting for ``GrouperModelAdmin`` to work properly.
    #:      In the change form the fields will be invisible.
    extra_grouping_fields: tuple[str, ...] = ()
    #: The content model class to be used. Defaults to the model class named like the grouper model class
    #: plus ``"Content"`` at the end from the same app as the grouper model class, e.g., ``BlogPostContent`` if
    #: the grouper is ``BlogPost``.
    content_model: type[models.Model] | None = None
    #: Name of the inverse relation field giving the set of content models belonging to a grouper model. Defaults to
    #: the first field found as an inverse relation. If you have more than one inverse relation please make sure
    #: to specify this field. An example would be if the blog post content model contained a many-to-many
    #: relationship to the grouper model for, say, related blog posts.
    content_related_field: str | None = None

    change_list_template = "admin/cms/grouper/change_list.html"
    change_form_template = "admin/cms/grouper/change_form.html"
    checks_class = GrouperModelAdminChecks

    class Media:
        js = (
            "admin/js/jquery.init.js",
            "cms/js/admin/language-selector.js",
        )

    EMPTY_CONTENT_VALUE = _("Empty content")
    LC_SORTED_FIELDS = (models.CharField,)
    CONTENT_OBJ_PK_ANNOTATION = "_content_obj_pk"

    _content_content_type = None

    #: Name of the GET parameter that selects a specific content object (by primary key) to be shown
    #: in the change view instead of the latest content. See :meth:`get_urls`.
    content_pk_url_param = "cms_content"
    #: Holds the specific content object requested via :attr:`content_pk_url_param` for the current
    #: request (thread-safe compatibility shim, see :meth:`get_grouping`).
    _requested_content_obj = _RequestedContentObjShim()

    def __init__(self, model, admin_site):
        # Request-derived grouping state (see Grouping) is stored per thread/async task:
        # ModelAdmin instances are shared between concurrent requests and must not carry it.
        self._local_grouping = Local()
        # Route legacy attribute access (e.g. self.language) through thread-safe shims.
        for field in self.extra_grouping_fields:
            inherited = getattr(type(self), field, _UNSET)
            if not isinstance(inherited, _GroupingFieldShim):
                setattr(type(self), field, _GroupingFieldShim(field, default=inherited))

        self._content_subquery_fields = []

        super().__init__(model, admin_site)

        # Identify content model
        if self.content_model is None:  # Did the Admin class specify a content model?
            # If not, try identifying using the naming convention {GrouperName}Content
            from django.apps import apps

            self.content_model = apps.get_model(f"{self.opts.app_label}.{self.model.__name__}Content")

        # Add an admin manager if the content model does not have one.
        if not hasattr(self.content_model, "admin_manager"):
            self.content_model.add_to_class("admin_manager", ContentAdminManager())

        # Find name of related field
        if not self.content_related_field:
            for related_object in model._meta.related_objects:
                if related_object.related_model is self.content_model:
                    self.content_related_field = related_object.get_accessor_name()
                    break
            else:
                raise ImproperlyConfigured(f"Related field for grouper model {model.__name__} not found")

        # Set grouper field name to snake case grouper model name if not given explicitly
        if not self.grouper_field_name:
            self.grouper_field_name = re.sub("(?!^)([A-Z]+)", r"_\1", self.model.__name__).lower()  # To snake case
        # Auto-generate ModelForm for Grouper if not specified (using GrouperAdminFormMixin)
        if not issubclass(self.form, _GrouperAdminFormMixin):
            self.form = type(
                "AutoGeneratedGrouperAdminForm",
                (GrouperAdminFormMixin(self.content_model), self.form),
                dict(),
            )

        # Generate accessor functions for content model fields
        content_field_names = modelform_factory(self.content_model, fields="__all__").base_fields.keys()
        for content_field in content_field_names:
            if (
                not hasattr(self, CONTENT_PREFIX + content_field)
                and content_field != self.grouper_field_name
                and content_field not in self.extra_grouping_fields
            ):
                if CONTENT_PREFIX + content_field in self.list_display:
                    # Identify content fields in list_display to annotate to queryset
                    self._content_subquery_fields.append(content_field)
                setattr(
                    self,
                    CONTENT_PREFIX + content_field,
                    self._getter_factory(content_field),
                )

    def _getter_factory(self, field: str) -> typing.Callable[[models.Model], typing.Any]:
        """Creates a getter function with ``short_description``, ``admin_order_field``, and ``boolean``
        properties suitable for the :attr:`~django.contrib.admin.ModelAdmin.list_display` field."""

        def getter(obj):
            return self.get_content_field(obj, field)

        getter.short_description = label_for_field(field, self.content_model)
        if field in self._content_subquery_fields:
            getter.admin_order_field = CONTENT_PREFIX + field
            if isinstance(self.content_model._meta.get_field(field), self.LC_SORTED_FIELDS):
                getter.admin_order_field += "__lc"
        getter.boolean = isinstance(self.content_model._meta.get_field(field), models.BooleanField)
        if not getter.boolean:
            # First non-boolean field will show empty content value by default.
            for display in getattr(self, "list_display", ()):
                if display == CONTENT_PREFIX + field:
                    getter.empty_value_display = self.EMPTY_CONTENT_VALUE
                if display.startswith(CONTENT_PREFIX):
                    break
        return getter

    def get_content_field(
        self,
        obj: models.Model,
        field_name: str,
        request: HttpRequest | None = None,
    ) -> typing.Any:
        """Retrieves the content of a field stored in the content model. If request is given extra
        grouping fields are processed before."""
        if hasattr(obj, CONTENT_PREFIX + field_name):
            # Annotated?
            return getattr(obj, CONTENT_PREFIX + field_name)
        if request:
            self.get_grouping_from_request(request)
        content_obj = self.get_content_obj(obj)
        return getattr(content_obj, field_name) if content_obj else None

    def _get_annotation(self):
        contents = self.content_model.admin_manager.latest_content(
            **{self.grouper_field_name: OuterRef("pk"), **self.current_content_filters}
        )
        annotation = {
            self.CONTENT_OBJ_PK_ANNOTATION: Subquery(contents.values("pk")[:1]),
        }
        for field_name in self._content_subquery_fields:
            annotation[CONTENT_PREFIX + field_name] = Subquery(contents.values(field_name)[:1])
            field = self.content_model._meta.get_field(field_name)
            if isinstance(field, DateField):
                # MySql needs an explicit cast, or it will return a string and not a date object
                annotation[CONTENT_PREFIX + field_name] = Cast(
                    annotation[CONTENT_PREFIX + field_name], field.__class__()
                )
            if isinstance(field, self.LC_SORTED_FIELDS):
                # Sort CharFields independently of case
                annotation[CONTENT_PREFIX + field_name + "__lc"] = functions.Lower(
                    Subquery(contents.values(field_name)[:1])
                )
        return annotation

    def can_change_content(self, request, content_obj):
        return self.get_content_readonly_message(request, content_obj) is None

    def get_content_readonly_message(self, request, content_obj):
        """Return ``None`` if the content can be changed, otherwise a human-readable
        message explaining why it is read-only.

        Permissions are owned by django CMS; editability (and its explanation) is
        owned by the content object's ``is_editable`` method. That method may return
        either a plain ``bool`` or a "rich bool" (e.g. from djangocms-versioning) that
        is falsy but also carries the reason(s) the editability checks failed via
        ``str()``. Plain bools carry no reason, so a generic message is used.
        """
        opts = self.content_model._meta
        perm = f"{opts.app_label}.{get_permission_codename('change' if content_obj else 'add', opts)}"
        if not request.user.has_perm(perm, content_obj):
            return _("You do not have permission to change this content.")
        editable = getattr(content_obj, "is_editable", lambda *_: True)(request)
        if editable:
            return None
        # ``editable`` is falsy: a plain bool offers no explanation, while a rich bool
        # exposes the reason(s) the checks failed via ``str()``.
        return " " if isinstance(editable, bool) else str(editable)  # " " is empty but truthy

    def get_queryset(self, request: HttpRequest) -> models.QuerySet:
        """Annotates content fields with the name "content__{field_name}" to the grouper queryset if
        for all content fields that appear in the"""
        qs = super().get_queryset(request).annotate(**self._get_annotation())
        prefetch = models.Prefetch(
            self.content_related_field,
            queryset=self.content_model.admin_manager.latest_content(),
            to_attr="_admin_prefetch_cache",
        )
        return qs.prefetch_related(prefetch)

    def get_language_from_request(self, request: HttpRequest) -> str:
        """Hook for get_language_from_request which by default uses the cms utility"""
        return get_language_from_request(request)

    def get_grouping_from_request(self, request: HttpRequest) -> Grouping:
        """Computes the grouping state from the request, caches it on the request, and
        publishes it for the current thread/async task.

        Called at every admin entry point (change list, change form, delete, and history
        views). Prefer :meth:`get_grouping` for read access - it reuses the cached state
        instead of recomputing it."""
        filters = {}
        for field in self.extra_grouping_fields:
            if hasattr(self, f"get_{field}_from_request"):
                filters[field] = getattr(self, f"get_{field}_from_request")(request)
            else:
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__} lacks method 'get_{field}_from_request(request)' to work with "
                    f"extra_grouping_fields={self.extra_grouping_fields}"
                )

        # A specific content object may be requested by its primary key. If so, show exactly that
        # content object (which may not be the latest one) and align the grouping fields with it so
        # that the form, its hidden fields, and the edit URLs stay consistent.
        requested_content_obj = self.get_requested_content_obj(request)
        if requested_content_obj is not None:
            for field in self.extra_grouping_fields:
                filters[field] = getattr(requested_content_obj, field)

        grouping = Grouping(filters, requested_content_obj)
        if not hasattr(request, "_cms_grouping_cache"):
            request._cms_grouping_cache = {}
        request._cms_grouping_cache[self] = grouping
        self._local_grouping.current = grouping
        return grouping

    def get_grouping(self, request: HttpRequest) -> Grouping:
        """Returns the grouping state for ``request``, computing it on first access.

        This is the request-scoped way to read grouping values - instead of the
        deprecated admin instance attributes (e.g. ``self.language``)::

            grouping = self.get_grouping(request)
            grouping.language                # value of an extra grouping field
            grouping.filters                 # e.g. {"language": "en"}
            grouping.requested_content_obj   # content object selected via GET, or None
        """
        grouping = getattr(request, "_cms_grouping_cache", {}).get(self)
        if grouping is None:
            return self.get_grouping_from_request(request)
        # (Re-)publish for legacy attribute access and request-less helpers.
        self._local_grouping.current = grouping
        return grouping

    def _current_grouping(self) -> Grouping | None:
        """The grouping most recently published for this thread/async task, if any."""
        return getattr(self._local_grouping, "current", None)

    def get_requested_content_obj(self, request: HttpRequest) -> models.Model | None:
        """Returns the content object requested by primary key via :attr:`content_pk_url_param`, or
        ``None`` if no (valid) content object was requested. Uses the ``admin_manager`` so that
        non-current content objects (e.g. older versions) can be shown."""
        content_pk = request.GET.get(self.content_pk_url_param)
        if not content_pk:
            return None
        try:
            return self.content_model.admin_manager.filter(pk=content_pk).first()
        except (ValueError, TypeError, ValidationError):
            # Invalid primary key for the content model: ignore and fall back to the latest content.
            return None

    @property
    def current_content_filters(self) -> dict[str, typing.Any]:
        """Filters needed to get the correct content model instance based on the grouping
        state published for the current thread/async task. Prefer
        ``self.get_grouping(request).filters`` where the request is available."""
        grouping = self._current_grouping()
        filters = grouping.filters if grouping else {}
        return {
            field: filters[field] if field in filters else self.get_extra_grouping_field(field)
            for field in self.extra_grouping_fields
        }

    def get_language(self) -> str:
        """Hook on how to get the current language. By default, use the grouping state
        published for the current thread/async task, otherwise let Django provide it."""
        grouping = self._current_grouping()
        if grouping is not None and "language" in grouping.filters:
            return grouping.filters["language"]
        return get_language()

    def get_language_tuple(self, site: Site | None = None) -> tuple[tuple[str, str], ...]:
        """Hook on how to get all available languages for the language selector."""
        return get_language_tuple(site_id=site.pk if site else None)

    def get_extra_grouping_field(self, field):
        """Retrieves the current value for grouping fields - by default by calling self.get_<field>, e.g.,
        self.get_language(). If those are not implemented, this method will fail."""
        if callable(getattr(self, f"get_{field}", None)):
            return getattr(self, f"get_{field}")()
        raise ValueError("Cannot get extra grouping field")

    def get_changelist(self, request: HttpRequest, **kwargs) -> type:
        """Allow for extra grouping fields as a non-filter parameter"""
        return type(
            GrouperChangeListBase.__name__,
            (GrouperChangeListBase,),
            dict(_extra_grouping_fields=self.extra_grouping_fields),
        )

    def get_urls(self) -> list:
        """Adds a change URL for the content model that redirects to the grouper change view showing
        the requested content object.

        This gives every content object a stable admin change URL (``admin:<app>_<content>_change``)
        that resolves through the unified grouper change form - without having to register a separate
        admin for the content model. If the content model already has its own admin (and hence already
        provides that URL name), the declaration is skipped so the existing admin keeps precedence.
        """
        urls = super().get_urls()
        if not self.admin_site.is_registered(self.content_model):
            opts = self.content_model._meta
            urls = [
                path(
                    "content/<path:object_id>/change/",
                    self.admin_site.admin_view(self.content_change_redirect_view),
                    name=f"{opts.app_label}_{opts.model_name}_change",
                ),
            ] + urls
        return urls

    @method_decorator(require_GET)
    def content_change_redirect_view(self, request: HttpRequest, object_id: str) -> HttpResponse:
        """Redirects from a content object's change URL to the grouper change view, selecting exactly
        that content object via the :attr:`content_pk_url_param` GET parameter.

        Limited to ``GET``: this is a navigation entry point only. The editable form lives at the
        grouper change view (which is where it is submitted), so a non-GET request here would
        otherwise be silently turned into a ``GET`` by the redirect and its payload discarded.
        """
        content_obj = get_object_or_404(self.content_model.admin_manager.all(), pk=object_id)
        grouper = getattr(content_obj, self.grouper_field_name)
        opts = grouper._meta
        url = admin_reverse(f"{opts.app_label}_{opts.model_name}_change", args=(grouper.pk,))
        params = {field: getattr(content_obj, field) for field in self.extra_grouping_fields}
        params[self.content_pk_url_param] = content_obj.pk
        return redirect(f"{url}?{urlencode(params)}")

    def get_changelist_instance(self, request: HttpRequest) -> GrouperChangeListBase:
        """Update grouping field properties and get changelist instance"""
        self.get_grouping_from_request(request)
        cl = super().get_changelist_instance(request)
        cl.current_language = self.get_language()
        if "language" in self.extra_grouping_fields:
            cl.available_languages = self.get_language_tuple(site=get_current_site(request))
        return cl

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict = None,
    ) -> HttpResponse:
        """Update grouping field properties for both add and change views"""
        self.get_grouping_from_request(request)
        return super().changeform_view(
            request,
            object_id,
            form_url,
            {
                **(extra_context or {}),
                **self.get_extra_context(request, object_id=object_id),
            },
        )

    def delete_view(
        self,
        request: HttpRequest,
        object_id: str,
        extra_context: dict | None = None,
    ) -> HttpResponse:
        """Update grouping field properties for delete view"""
        self.get_grouping_from_request(request)
        return super().delete_view(request, object_id, extra_context)

    def history_view(
        self,
        request: HttpRequest,
        object_id: str,
        extra_context: dict | None = None,
    ) -> HttpResponse:
        """Update grouping field properties for history view"""
        self.get_grouping_from_request(request)
        return super().history_view(request, object_id, extra_context)

    def get_preserved_filters(self, request: HttpRequest) -> str:
        """Always preserve grouping get parameters! Also, add them to changelist filters:
        * Save and continue will keep the grouping parameters
        * Save and returning to changelist will keep the grouping parameters
        """
        preserved_filters = dict(parse_qsl(super().get_preserved_filters(request)))
        # Extra grouping fields from the published grouping state
        grouping = self._current_grouping()
        grouping_filters = {}
        for field in self.extra_grouping_fields:
            value = grouping.filters.get(field) if grouping else None
            if "field" not in preserved_filters:
                grouping_filters[field] = value
        preserved_filters.update(grouping_filters)
        if "_changelist_filters" not in preserved_filters:
            preserved_filters["_changelist_filters"] = urlencode(grouping_filters)
        return urlencode(preserved_filters)

    def get_extra_context(self, request: HttpRequest, object_id: str | None = None) -> dict[str, typing.Any]:
        """Provide the grouping fields to the change view."""
        if object_id:
            # Instance provided? Get corresponding postconent
            obj = get_object_or_404(self.model, pk=object_id)
            content_instance = self.get_content_obj(obj)
            title = _("%(object_name)s Properties") % dict(object_name=obj._meta.verbose_name.capitalize())
        else:
            obj = None
            content_instance = None
            title = _("Add new %(object_name)s") % dict(object_name=self.model._meta.verbose_name)

        if content_instance:
            subtitle = str(content_instance)
        else:
            subtitle = _("Add content")

        extra_context = {
            "changed_message": _(
                'Content for the current language has been changed. Click "Cancel" to '
                'return to the form and save changes. Click "OK" to discard changes.'
            ),
            "title": title,
            "content_instance": content_instance,
            "subtitle": subtitle,
        }

        """Provide the grouping fields to edit"""
        if "language" in self.extra_grouping_fields:
            language = self.get_grouping(request).language
            if obj:
                filled_languages = self.get_content_objects(obj).values_list("language", flat=True).distinct()
            else:
                filled_languages = []

            site = get_current_site(request)
            if self.is_latest_content_obj(content_instance, obj):
                # Only offer the language selector for the latest content. Switching the
                # language always navigates to the latest content of the target language,
                # so for an older content object switching languages back and forth would
                # silently bring up a different (the latest) content object - confusing UX.
                extra_context["language_tabs"] = self.get_language_tuple(site=site)
            extra_context["language"] = language
            extra_context["filled_languages"] = filled_languages
            readonly_message = self.get_content_readonly_message(request, content_instance)
            extra_context["content_readonly_message"] = readonly_message
            extra_context["can_change_content_obj"] = readonly_message is None
            if content_instance is None:
                subtitle = _("Add %(language)s content") % dict(
                    language=get_language_dict(site_id=site.pk).get(language)
                )
                extra_context["subtitle"] = subtitle

        # TODO: Add context for other grouping fields to be shown as a dropdown
        return extra_context

    def get_form(self, request: HttpRequest, obj: models.Model | None = None, **kwargs) -> type:
        """Adds the language from the request to the form class"""
        self.get_grouping_from_request(request)  # direct entry point from django admin
        form_class = super().get_form(request, obj, **kwargs)
        form_class = type(form_class)(
            form_class.__name__,
            (form_class,),
            {"_admin": self, "_request": request},
        )

        for field in self.extra_grouping_fields:
            form_class.base_fields[CONTENT_PREFIX + field].widget = forms.HiddenInput()

        if (getattr(form_class._meta, "fields", None) or "__all__") != "__all__":
            for field in self.extra_grouping_fields:
                if CONTENT_PREFIX + field not in form_class._meta.fields:
                    raise ImproperlyConfigured(
                        f"{self.__class__.__name__} needs to include all "
                        f"extra_grouping_fields={self.extra_grouping_fields} in its admin. {field} is missing."
                    )
        return form_class

    def get_changelist_form(self, request: HttpRequest, **kwargs) -> type:
        """Return a grouper form capable of editing grouper and content fields."""
        self.get_grouping_from_request(request)
        content_id_field = forms.ModelChoiceField(
            queryset=self.content_model.admin_manager.all(),
            required=False,
            widget=forms.HiddenInput(),
        )
        editable_content_fields = {
            field for field in self.list_editable if field.startswith(CONTENT_PREFIX)
        }
        form_attributes = {
            "_admin": self,
            "_request": request,
            "_content_object_id": content_id_field,
        }
        form_attributes.update(
            {
                CONTENT_PREFIX + field: None
                for field in self.form._content_fields
                if CONTENT_PREFIX + field not in editable_content_fields
            }
        )
        form_class = type(self.form)(
            self.form.__name__,
            (self.form,),
            form_attributes,
        )
        return super().get_changelist_form(request, form=form_class, **kwargs)

    def get_changelist_formset(self, request: HttpRequest, **kwargs) -> type:
        """Include the hidden content identity in the changelist formset."""
        defaults = {
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
            **kwargs,
        }
        return modelformset_factory(
            self.model,
            self.get_changelist_form(request),
            extra=0,
            fields=(*self.list_editable, "_content_object_id"),
            **defaults,
        )

    # Admin list actions defined below:
    # * View button that takes the user to the preview endpoint of the content model
    # * Settings button that lets the user change the grouper AND the content model
    #   using one form
    def _get_view_action(self, obj: models.Model, request: HttpRequest) -> str:
        if not is_editable_model(self.content_model):
            return ""

        view_url = self.view_on_site(obj)
        if view_url:
            return self.admin_action_button(
                url=view_url,
                icon="view",
                title=_("Preview"),
                disabled=not view_url,
                keepsideframe=False,
                name="view",
            )
        return ""

    def _has_content(self, obj: models.Model) -> bool:
        if self._is_content_obj(obj):
            return True  # pragma: no cover
        if hasattr(obj, self.CONTENT_OBJ_PK_ANNOTATION):
            return getattr(obj, self.CONTENT_OBJ_PK_ANNOTATION) is not None
        return self.get_content_obj(obj) is not None  # pragma: no cover

    def _get_settings_action(self, obj: models.Model, request: HttpRequest) -> str:
        edit_url = admin_reverse(f"{obj._meta.app_label}_{obj._meta.model_name}_change", args=(obj.pk,))
        edit_url += f"?{urlencode(self.current_content_filters)}"
        has_content = self._has_content(obj)
        return self.admin_action_button(
            url=edit_url,
            icon="settings" if has_content else "plus",
            title=_("Settings") if has_content else _("Add content"),
            disabled=not edit_url,
            name="settings",
        )

    def get_actions_list(self) -> list:
        return [self._get_view_action, self._get_settings_action]

    def endpoint_url(self, admin: str, obj: models.Model) -> str:
        if self._is_content_obj(obj):
            cls = obj.__class__
            pk = obj.pk
        else:
            content = self.get_content_obj(obj)
            cls = content.__class__
            pk = content.pk

        if self._content_content_type is None:
            from django.contrib.contenttypes.models import ContentType

            self._content_content_type = ContentType.objects.get_for_model(cls).pk
        try:
            return admin_reverse(admin, args=[self._content_content_type, pk])
        except NoReverseMatch:
            return ""

    def _is_content_obj(self, obj: models.Model) -> bool:
        return isinstance(obj, self.content_model)

    def _get_content_queryset(self, obj: models.Model) -> models.QuerySet:
        return getattr(obj, self.content_related_field)(manager="admin_manager").latest_content()

    def get_content_obj(self, obj: models.Model | None) -> models.Model | None:
        if obj is None or self._is_content_obj(obj):
            return obj

        # A specific content object was requested by primary key? Show exactly that object as long
        # as it belongs to the grouper being edited (instead of the latest content).
        requested = self._requested_content_obj
        if requested is not None and getattr(requested, f"{self.grouper_field_name}_id", None) == obj.pk:
            return requested

        if not hasattr(obj, "_grouper_admin_content_obj_cache"):
            # Check prefetch cache
            if hasattr(obj, "_admin_prefetch_cache"):
                for content_obj in obj._admin_prefetch_cache:
                    if all(
                        getattr(content_obj, key, None) == value for key, value in self.current_content_filters.items()
                    ):
                        obj._grouper_admin_content_obj_cache = content_obj
                        return content_obj
                obj._grouper_admin_content_obj_cache = None  # no hit
                return None
            obj._grouper_admin_content_obj_cache = (
                self._get_content_queryset(obj).filter(**self.current_content_filters).first()
            )
        return obj._grouper_admin_content_obj_cache

    def get_content_objects(self, obj: models.Model | None) -> models.QuerySet:
        if obj is None:
            return None
        if self._is_content_obj(obj):
            # Already content object? First get grouper and then all content objects
            return self.get_content_objects(self.get_grouper_obj(obj))
        return self._get_content_queryset(obj)

    def is_latest_content_obj(self, content_obj: models.Model | None, obj: models.Model | None = None) -> bool:
        """Hook to decide whether ``content_obj`` is the latest content for its grouper and the
        current grouping fields (e.g. language).

        By default :meth:`get_content_obj` returns the latest content, so this is always ``True``.
        Versioning packages, however, may show an older content object in the change form. In that
        case switching grouping fields (such as the language) navigates to the latest content of the
        target value, so switching back and forth would not return to the same content object. The
        change form therefore hides the grouping selectors when an older content object is shown.
        """
        if content_obj is None:
            # The add view always edits the (still non-existing) latest content.
            return True
        latest = self.get_content_objects(obj or content_obj).filter(**self.current_content_filters).first()
        return latest is None or latest.pk == content_obj.pk

    def clear_content_cache(self) -> None:
        # Content objects are now stored in the object, no cache clear for admin class necessary
        pass

    def get_grouper_obj(self, obj: models.Model) -> models.Model:
        """Get the admin object. If obj is a content object assume that the admin object
        resides in the field named after the admin model. The admin model name must be
        the same as the content model name minus "Content" at the end."""
        if self._is_content_obj(obj):
            field_name = obj.__class__.__name__[-7:].lower()
            return getattr(obj, field_name)
        return obj

    def view_on_site(self, obj: models.Model) -> str | None:
        # Adds the View on Site button to the admin
        content_obj = self.get_content_obj(obj)
        if content_obj is not None and is_editable_model(content_obj.__class__):
            # Try getting the language from the content object
            return get_object_edit_url(content_obj, language=getattr(content_obj, "language", None))
        return None

    def get_readonly_fields(self, request: HttpRequest, obj: models.Model | None = None):
        """Allow access to content fields to be controlled by a method "can_change_content":
        This allows versioned content to be protected if needed"""
        # First, get read-only fields for grouper
        fields = super().get_readonly_fields(request, obj)
        content_obj = self.get_content_obj(obj)
        if not self.can_change_content(request, content_obj):
            # Only allow content object fields to be edited if user can change them
            fields = [
                *fields,
                *(
                    CONTENT_PREFIX + field
                    for field in self.form._content_fields
                    if field != self.grouper_field_name and field not in self.extra_grouping_fields
                ),
            ]
        return fields

    def get_prepopulated_fields(self, request: HttpRequest, obj: models.Model | None = None) -> dict:
        """Drop prepopulated entries whose key is read-only.

        ``AdminForm`` looks up every prepopulated key in the rendered form, so an entry
        keyed on a field that ``get_readonly_fields`` returns would raise ``KeyError``.
        Filter dynamically against the class attribute so subclasses can keep declaring
        ``prepopulated_fields`` the normal way.
        """
        prepopulated_fields = super().get_prepopulated_fields(request, obj)
        if not prepopulated_fields:
            return prepopulated_fields
        readonly = set(self.get_readonly_fields(request, obj))
        return {key: value for key, value in prepopulated_fields.items() if key not in readonly}

    def save_model(self, request: HttpRequest, obj: models.Model, form: forms.Form, change: bool) -> None:
        """Save/create both grouper and content object"""
        super().save_model(request, obj or form.instance, form, change)
        if not hasattr(form, "_content_fields"):
            return
        content_dict = {
            field: form.cleaned_data[CONTENT_PREFIX + field]
            for field in form._content_fields
            if CONTENT_PREFIX + field in form.cleaned_data
        }
        if not content_dict:
            return
        if form._content_instance is None or form._content_instance.pk is None:
            content_dict[self.grouper_field_name] = form.instance
            content_dict.update(self.current_content_filters)
            if hasattr(form._content_model.objects, "with_user"):
                # Create new using with_user syntax if available ...
                form._content_model.objects.with_user(request.user).create(**content_dict)
            else:  # pragma: no cover
                # ... without otherwise
                form._content_model.objects.create(**content_dict)
        elif self.can_change_content(request, form._content_instance):
            # Update content instance (only if can_change_content allows it)
            for key, value in content_dict.items():
                setattr(form._content_instance, key, value)
            # Finally force grouper field to point to grouper
            setattr(form._content_instance, self.grouper_field_name, obj)
            form._content_instance.save()

    def get_search_fields(self, request):
        """Return search fields for either grouper model or content model"""
        content_search_fields = []
        grouper_search_fields = []
        for field_name in self.search_fields:
            if field_name.startswith(CONTENT_PREFIX):
                content_search_fields.append(field_name[len(CONTENT_PREFIX) :])
            else:
                grouper_search_fields.append(field_name)

        if getattr(request, "_content_fields", False):
            return content_search_fields

        return grouper_search_fields

    def get_search_results(self, request, queryset, search_term):
        grouper_search_result, may_have_duplicate_grouper = super().get_search_results(request, queryset, search_term)

        search_result_from_content, may_have_duplicate_content = self._get_content_search_result(
            request, queryset, search_term
        )

        return grouper_search_result | search_result_from_content, (
            may_have_duplicate_grouper & may_have_duplicate_content
        )

    def _get_content_search_result(self, request, queryset, search_term):
        """Get search results from content model"""
        try:
            # Set flag on request object to get the content search fields. `get_search_results` will call
            # `get_search_fields` to get the content search fields.
            request._content_fields = True
            content_queryset = self.content_model.admin_manager.all()
            if self.get_search_fields(request):
                content_search_result, __ = super().get_search_results(request, content_queryset, search_term)
            else:
                content_search_result = self.content_model.admin_manager.none()
            search_result_from_content = queryset.filter(
                id__in=content_search_result.values_list(f"{self.grouper_field_name}_id", flat=True)
            )
        finally:
            request._content_fields = False
        return search_result_from_content, False


class _ContentIdentityWidget(forms.Widget):
    """Render a content field together with its changelist content identity."""

    def __init__(self, widget, content_field_name):
        super().__init__(attrs=widget.attrs)
        self.widget = widget
        self.content_field_name = content_field_name
        self.content_object_id = None

    @property
    def media(self):
        return self.widget.media

    def id_for_label(self, id_):
        return self.widget.id_for_label(id_)

    def value_from_datadict(self, data, files, name):
        return self.widget.value_from_datadict(data, files, name)

    def value_omitted_from_data(self, data, files, name):
        return self.widget.value_omitted_from_data(data, files, name)

    def render(self, name, value, attrs=None, renderer=None):
        field = self.widget.render(name, value, attrs=attrs, renderer=renderer)
        prefix = name[: -len(self.content_field_name)]
        identity = forms.HiddenInput().render(
            f"{prefix}_content_object_id",
            self.content_object_id,
            renderer=renderer,
        )
        return format_html("{}{}", field, identity)


class _GrouperAdminFormMixin:
    _content_fields: list = []

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "_admin"):
            raise ValueError(
                "GrouperModelFormMixin forms can only be instantiated if the class attribute '_admin' "
                "has been set and points to the instantiating admin instance."
            )

        if "instance" in kwargs and kwargs["instance"]:
            # Instance provided? Initialize fields from content model
            instance = kwargs["instance"]
            self._content_instance = self._admin.get_content_obj(instance)
            if self._content_instance:
                kwargs["initial"] = {
                    **{
                        CONTENT_PREFIX + field: getattr(self._content_instance, field)
                        for field in self._content_fields
                        if CONTENT_PREFIX + field in self.base_fields
                    },
                    **kwargs.get("initial", {}),
                }
                if "_content_object_id" in self.base_fields:
                    kwargs["initial"]["_content_object_id"] = self._content_instance
        else:
            self._content_instance = None

        # set values for grouping fields
        kwargs["initial"] = {
            **{CONTENT_PREFIX + key: value for key, value in self._admin.current_content_filters.items()},
            **kwargs.get("initial", {}),
        }

        # The actual init
        super().__init__(*args, **kwargs)

        editable_content_fields = [
            field for field in self.fields if field.startswith(CONTENT_PREFIX)
        ]
        if "_content_object_id" in self.fields and editable_content_fields:
            field_name = editable_content_fields[0]
            widget = _ContentIdentityWidget(self.fields[field_name].widget, field_name)
            widget.content_object_id = self._content_instance.pk if self._content_instance else None
            self.fields[field_name].widget = widget

        # Hide grouper foreign key
        grouper_field_name = CONTENT_PREFIX + self._admin.grouper_field_name
        if grouper_field_name in self.fields:
            self.fields[grouper_field_name].widget = forms.HiddenInput()
            # Will be set on admin model save
            self.fields[grouper_field_name].required = False
        self.update_labels(self._content_fields)

    def update_labels(self, fields: list[str]) -> None:
        """Adds a language indicator to field labels"""
        if "language" in self._admin.extra_grouping_fields:
            site = get_current_site(self._request)
            language_dict = get_language_dict(site_id=site.pk if site else None)
            language_postfix = f" ({language_dict[self._admin.get_grouping(self._request).language]})"
            for field in fields:
                if CONTENT_PREFIX + field in self.fields:
                    # Fields contained in field list?
                    self.fields[CONTENT_PREFIX + field].label += language_postfix
                else:
                    # Get default from content model
                    if self._meta.labels is None:
                        self._meta.labels = {}
                    self._meta.labels.setdefault(
                        CONTENT_PREFIX + field,
                        label_for_field(field, self._admin.content_model) + language_postfix,
                    )

    def clean(self) -> dict:
        site = get_current_site(self._request)
        if f"{CONTENT_PREFIX}language" in self.cleaned_data and self.cleaned_data[
            f"{CONTENT_PREFIX}language"
        ] not in get_language_list(site_id=site.pk):
            raise ValidationError(
                _("Invalid language %(value)s. This form cannot be processed. Try changing languages."),
                params=dict(value=self.cleaned_data.get("language", _("<unspecified>"))),
                code="invalid-language",
            )
        cleaned_data = super().clean()
        if "_content_object_id" in cleaned_data:
            content_obj = cleaned_data["_content_object_id"]
            if content_obj is not None:
                grouper_id = getattr(content_obj, f"{self._admin.grouper_field_name}_id")
                grouping_matches = all(
                    getattr(content_obj, field) == value
                    for field, value in self._admin.current_content_filters.items()
                )
                if grouper_id != self.instance.pk or not grouping_matches:
                    raise ValidationError(_("The selected content does not match this object and grouping."))
                self._content_instance = content_obj
            if any(field.startswith(CONTENT_PREFIX) for field in self.changed_data) and not self._admin.can_change_content(
                self._request, content_obj
            ):
                raise ValidationError(_("You do not have permission to change this content."))
        return cleaned_data


class GrouperAdminFormMixin:
    """Actually a factory class that creates the GrouperAdminFormMixin. Pass the Model or ModelForm as a
    parameter::

        class MyGrouperModelForm(GrouperModelFormMixin(ContentModel), forms.ModelForm):
            model = GrouperModel
            ...

    .. info::

        For most cases you will not need to use this mixin. :class:`~cms.admin.utils.GrouperModelAdmin` automatically
        adds the mixin to the form provided to it or the standard :class:`~django.forms.ModelForm`. As a results, you
        can just use a subclass of :class:`~django.forms.ModelForm` for :class:`~cms.admin.utils.GrouperModelAdmin`.

    .. warning::

        This mixin only works when used together with :class:`~cms.admin.utils.GrouperModelAdmin`.
    """

    def __new__(cls, content_model: models.base.ModelBase) -> type:
        model_form = modelform_factory(content_model, fields="__all__")
        base_fields = {CONTENT_PREFIX + key: value for key, value in model_form.base_fields.items()}
        return forms.forms.DeclarativeFieldsMetaclass(
            GrouperAdminFormMixin.__name__,
            (_GrouperAdminFormMixin,),
            {
                **base_fields,  # inherit the content model form's fields
                "_content_model": content_model,  # remember the model and
                "_content_fields": model_form.base_fields.keys(),  # fields that come from the content form
            },
        )

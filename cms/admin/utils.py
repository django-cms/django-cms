import re
import typing
from urllib.parse import parse_qsl

from django import forms
from django.contrib.admin import ModelAdmin
from django.contrib.admin.utils import label_for_field
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.forms import modelform_factory
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import NoReverseMatch
from django.utils.functional import cached_property
from django.utils.html import format_html_join
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import get_language, gettext_lazy as _

from cms.models.managers import ContentAdminManager
from cms.toolbar.utils import get_object_preview_url
from cms.utils import get_language_from_request
from cms.utils.i18n import get_language_dict, get_language_tuple
from cms.utils.urlutils import admin_reverse, static_with_version

#: Prefix for content model fields to be added to the grouper admin and to the change form.
CONTENT_PREFIX = "content__"


class ChangeListActionsMixin(metaclass=forms.MediaDefiningClass):
    """AdminListActionsMixin is a mixin for the ModelAdmin class. It adds the ability to have
    action buttons and a burger menu in the admin's change list view. Unlike actions that affect
    multiple listed items the list action buttons only affect one item at a time.

    Use :meth:`~cms.admin.utils.AdminListActionsMixin.get_action_list` to register actions and
    :meth:`~cms.admin.utils.AdminListActionsMixin.admin_action_button` to define the button
    behavior.

    To activate the actions make sure ``"admin_list_actions"`` is in the admin classes
    :prop:`~django.contrib.admin.ModelAdmin.list_display` property.
    """

    class Media:
        js = (
            "admin/js/jquery.init.js",
            "cms/js/admin/actions.js",
        )
        css = {"all": (static_with_version("cms/css/cms.admin.css"),)}

    def get_actions_list(
        self,
    ) -> typing.List[typing.Callable[[models.Model, HttpRequest], str]]:
        """Collect list actions from implemented methods and return as list. Make sure to call
        it's ``super()`` instance when overwriting::

            class MyModelAdmin(admin.ModelAdmin):
                ...

                def get_actions_list(self):
                    return super().get_actions_list() + [self.my_first_action, self.my_second_action]
        """
        return []

    def get_admin_list_actions(
        self, request: HttpRequest
    ) -> typing.Callable[[models.Model], str]:
        """Method to register the admin action menu with the admin's list display

        Usage (in your model admin)::

            class MyModelAdmin(AdminActionsMixin, admin.ModelAdmin):
                ...
                list_display = ('name', ..., 'admin_list_actions')

        """

        def list_actions(obj: models.Model) -> str:
            """The name of this inner function must not change. css styling and js depends on it."""
            EMPTY = mark_safe('<span class="cms-empty-action"></span>')
            return format_html_join(
                "",
                "{}",
                (
                    (action(obj, request) or EMPTY,)
                    for action in self.get_actions_list()
                ),
            )

        list_actions.short_description = _("Actions")
        return list_actions

    def admin_list_actions(self, obj: models.Model) -> None:
        raise ValueError(
            'ModelAdmin.display_list contains "admin_list_actions" as a placeholder for list action icons. '
            'AdminListActionsMixin is not loaded, however. If you implement "get_list_display" make '
            "sure it calls super().get_list_display."
        )  # pragma: no cover

    def get_list_display(
        self, request: HttpRequest
    ) -> typing.Tuple[typing.Union[str, typing.Callable[[models.Model], str]], ...]:
        list_display = super().get_list_display(request)
        return tuple(
            self.get_admin_list_actions(request)
            if item == "admin_list_actions"
            else item
            for item in list_display
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
        """Returns a generic button supported by the AdminListActionsMixin.

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
                        return self.admin_action_button(url, "info",  _("View usage"), disabled=disabled)
                    return ""  # No button

        """
        return render_to_string(
            "admin/cms/icons/base.html",
            {
                "url": url or "",
                "icon": icon,
                "action": action,
                "disabled": disabled,
                "keepsideframe": keepsideframe,
                "title": title,
                "burger_menu": burger_menu,
                "name": name,
            },
        )


class GrouperChangeListBase(ChangeList):
    """Subclass ChangeList to disregard grouping fields get parameter as filter"""

    _extra_grouping_fields = []

    def get_filters_params(self, params: typing.Optional[dict] = None):
        lookup_params = super().get_filters_params(params)
        for field in self._extra_grouping_fields:
            if field in lookup_params:
                del lookup_params[field]
        return lookup_params


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
    grouper_field_name: typing.Optional[str] = None
    #: Indicates additional grouping fields such as ``"language"`` for example. Additional grouping fields create
    #: tabs in the change form and a dropdown menu in the change list view.
    #:
    #: .. note::
    #:
    #:      All fields serving as extra grouping fields must be part of the admin's
    #:      :attr:`~django.contrib.admin.ModelAdmin.fieldsets` setting for ``GrouperModelAdmin`` to work properly.
    #:      In the change form the fields will be invisible.
    extra_grouping_fields: typing.Tuple[str, ...] = ()
    #: The content model class to be used. Defaults to the model class named like the grouper model class
    #: plus ``"Content"`` at the end from the same app as the grouper model class, e.g., ``BlogPostContent`` if
    #: the grouper is ``BlogPost``.
    content_model: typing.Optional[models.Model] = None
    #: Name of the inverse relation field giving the set of content models belonging to a grouper model. Defaults to
    #: the first field found as an inverse relation. If you have more than one inverse relation please make sure
    #: to specify this field. An example would be if the blog post content model contained a many-to-many
    #: relationship to the grouper model for, say, related blog posts.
    content_related_field: typing.Optional[str] = None

    change_list_template = "admin/cms/grouper/change_list.html"
    change_form_template = "admin/cms/grouper/change_form.html"

    class Media:
        js = (
            "admin/js/jquery.init.js",
            "cms/js/admin/language-selector.js",
        )

    EMPTY_CONTENT_VALUE = _("Empty content")

    _content_obj_cache = {}
    _content_cache_request_hash = None
    _content_qs_cache = {}
    _content_content_type = None

    def __init__(self, model, admin_site):
        super().__init__(model, admin_site)

        # Identify content model
        if self.content_model is None:  # Did the Admin class specify a content model?
            # If not, try identifying using the naming convention {GrouperName}Content
            from django.apps import apps

            self.content_model = apps.get_model(
                f"{self.opts.app_label}.{self.model.__name__}Content"
            )

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
                raise ImproperlyConfigured(
                    f"Related field for grouper model {model.__name__} not found"
                )

        # Auto-generate ModelForm for Grouper if not specified (using GrouperAdminFormMixin)
        if not issubclass(self.form, _GrouperAdminFormMixin):
            self.form = type(
                "AutoGeneratedGrouperAdminForm",
                (GrouperAdminFormMixin(self.content_model), self.form),
                dict(),
            )

        # Generate accessor functions for content model fields
        for content_field in self.form._content_fields:
            if (
                not hasattr(self, CONTENT_PREFIX + content_field)
                and content_field != self._grouper_field_name  # noqa: W504
                and content_field not in self.extra_grouping_fields  # noqa: W504
            ):
                setattr(
                    self,
                    CONTENT_PREFIX + content_field,
                    self._getter_factory(content_field),
                )

    def _getter_factory(self, field: str) -> typing.Callable[[models.Model], typing.Any]:
        """Creates a getter function with ``short_description`` and ``boolean`` properties suitable
        for the :attr:`~django.contrib.admin.ModelAdmin.list_display` field."""
        getter = lambda obj: self.get_content_field(obj, field, request=None)
        getter.short_description = label_for_field(field, self.content_model)
        getter.boolean = isinstance(
            self.form.base_fields[CONTENT_PREFIX + field], forms.BooleanField
        )
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
        request: typing.Optional[HttpRequest] = None,
    ) -> typing.Any:
        """Retrieves the content of a field stored in the content model. If request is given extra
        grouping fields are processed before."""
        if request:
            self.get_grouping_from_request(request)
        content_obj = self.get_content_obj(obj)
        return getattr(content_obj, field_name) if content_obj else None

    @cached_property
    def _grouper_field_name(self) -> str:
        """Property or lower case model name"""
        if getattr(self, "grouper_field_name", None):
            return self.grouper_field_name
        return re.sub("(?!^)([A-Z]+)", r"_\1", self.model.__name__).lower()
        return self.model.__name__.lower()

    def get_language_from_request(self, request: HttpRequest) -> str:
        """Hook for get_language_from_request which by default uses the cms utility"""
        return get_language_from_request(request)

    def get_grouping_from_request(self, request: HttpRequest) -> None:
        """Retrieves the current grouping selectors from the request"""
        if hash(request) != self._content_cache_request_hash:
            self._content_cache_request_hash = hash(request)
            self.clear_content_cache()
        for field in self.extra_grouping_fields:
            if hasattr(self, f"get_{field}_from_request"):
                value = getattr(self, f"get_{field}_from_request")(request)
            else:
                raise ImproperlyConfigured(
                    f"{self.__class__.__name__} lacks method 'get_{field}_from_request(request)' to work with "
                    f"extra_grouping_fields={self.extra_grouping_fields}"
                )
            if value != getattr(self, field, None):
                setattr(self, field, value)

    @property
    def current_content_filters(self) -> typing.Dict[str, typing.Any]:
        """Filters needed to get the correct content model instance"""
        return {field: getattr(self, field) for field in self.extra_grouping_fields}

    def get_language(self) -> str:
        """Hook on how to get the current language. By default, Django provides it."""
        return get_language()

    def get_language_tuple(self) -> typing.Tuple[typing.Tuple[str, str], ...]:
        """Hook on how to get all available languages for the language selector."""
        return get_language_tuple()

    def get_changelist(self, request: HttpRequest, **kwargs) -> type:
        """Allow for extra grouping fields as a non-filter parameter"""
        return type(
            GrouperChangeListBase.__name__,
            (GrouperChangeListBase,),
            dict(_extra_grouping_fields=self.extra_grouping_fields),
        )

    def get_changelist_instance(self, request: HttpRequest) -> GrouperChangeListBase:
        """Update grouping field properties and get changelist instance"""
        self.get_grouping_from_request(request)
        return super().get_changelist_instance(request)

    def changeform_view(
        self,
        request: HttpRequest,
        object_id: typing.Optional[str] = None,
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
        extra_context: typing.Optional[dict] = None,
    ) -> HttpResponse:
        """Update grouping field properties for delete view"""
        self.get_grouping_from_request(request)
        return super().delete_view(request, object_id, extra_context)

    def history_view(
        self,
        request: HttpRequest,
        object_id: str,
        extra_context: typing.Optional[dict] = None,
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
        # Extra grouping fields from property
        grouping_filters = {}
        for field in self.extra_grouping_fields:
            value = getattr(self, field, None)
            if "field" not in preserved_filters:
                grouping_filters[field] = value
        preserved_filters.update(grouping_filters)
        if "_changelist_filters" not in preserved_filters:
            preserved_filters["_changelist_filters"] = urlencode(grouping_filters)
        return urlencode(preserved_filters)

    def get_extra_context(
        self, request: HttpRequest, object_id: typing.Optional[str] = None
    ) -> typing.Dict[str, typing.Any]:
        """Provide the grouping fields to the change view."""
        if object_id:
            # Instance provided? Get corresponding postconent
            obj = get_object_or_404(self.model, pk=object_id)
            content_instance = self.get_content_obj(obj)
            title = _("%(object_name)s Properties") % dict(
                object_name=obj._meta.verbose_name.capitalize()
            )
        else:
            obj = None
            content_instance = None
            title = _("Add new %(object_name)s") % dict(
                object_name=self.model._meta.verbose_name
            )

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
            language = self.language
            if obj:
                filled_languages = (
                    self.get_content_objects(obj)
                    .values_list("language", flat=True)
                    .distinct()
                )
            else:
                filled_languages = []

            extra_context["language_tabs"] = self.get_language_tuple()
            extra_context["language"] = language
            extra_context["filled_languages"] = filled_languages
            if content_instance is None:
                subtitle = _("Add %(language)s content") % dict(
                    language=get_language_dict().get(self.language)
                )
                extra_context["subtitle"] = subtitle

        # TODO: Add context for other grouping fields to be shown as a dropdown
        return extra_context

    def get_form(
        self, request: HttpRequest, obj: typing.Optional[models.Model] = None, **kwargs
    ) -> type:
        """Adds the language from the request to the form class"""
        form_class = super().get_form(request, obj, **kwargs)
        form_class._admin = self
        form_class._request = request

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

    # Admin list actions defined below:
    # * View button that takes the user to the preview endpoint of the content model
    # * Settings button that lets the user change the grouper AND the content model
    #   using one form
    def _get_view_action(self, obj, request: HttpRequest) -> str:
        if self.get_content_obj(obj):
            view_url = self.view_on_site(self.get_content_obj(obj))
            return self.admin_action_button(
                url=view_url,
                icon="view",
                title=_("Preview"),
                disabled=not view_url,
                keepsideframe=False,
                name="view",
            )
        return ""

    def _get_settings_action(self, obj: models.Model, request: HttpRequest) -> str:
        edit_url = admin_reverse(
            f"{obj._meta.app_label}_{obj._meta.model_name}_change", args=(obj.pk,)
        )
        edit_url += f"?{urlencode(self.current_content_filters)}"
        return self.admin_action_button(
            url=edit_url,
            icon="settings" if self.get_content_obj(obj) else "plus",
            title=_("Settings") if self.get_content_obj(obj) else _("Add content"),
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
        if obj not in self._content_qs_cache:
            self._content_qs_cache[obj] = getattr(obj, self.content_related_field)(
                manager="admin_manager"
            ).latest_content()
        return self._content_qs_cache[obj]

    def get_content_obj(
        self, obj: typing.Optional[models.Model]
    ) -> typing.Optional[models.Model]:
        if obj is None or self._is_content_obj(obj):
            return obj
        else:
            if obj not in self._content_obj_cache:
                self._content_obj_cache[obj] = (
                    self._get_content_queryset(obj)
                    .filter(**self.current_content_filters)
                    .first()
                )
            return self._content_obj_cache[obj]

    def get_content_objects(
        self, obj: typing.Optional[models.Model]
    ) -> models.QuerySet:
        if obj is None:
            return None
        if self._is_content_obj(obj):
            # Already content object? First get grouper and then all content objects
            return self.get_content_objects(self.get_grouper_obj(obj))
        return self._get_content_queryset(obj)

    def clear_content_cache(self) -> None:
        """Clear cache, e.g., for a new request"""
        self._content_obj_cache = {}
        self._content_qs_cache = {}

    def get_grouper_obj(self, obj: models.Model) -> models.Model:
        """Get the admin object. If obj is a content object assume that the admin object
        resides in the field named after the admin model. The admin model name must be
        the same as the content model name minus "Content" at the end."""
        if self._is_content_obj(obj):
            field_name = obj.__class__.__name__[-7:].lower()
            return getattr(obj, field_name)
        return obj

    def view_on_site(self, obj: models.Model) -> typing.Optional[str]:
        # Adds the View on Site button to the admin
        content_obj = self.get_content_obj(obj)
        return get_object_preview_url(content_obj) if content_obj else None

    def get_readonly_fields(
        self, request: HttpRequest, obj: typing.Optional[models.Model] = None
    ):
        """Allow access to content fields to be controlled by a method "can_change_content":
        This allows versioned content to be protected if needed"""
        # First, get read-only fields for grouper
        fields = super().get_readonly_fields(request, obj)
        if hasattr(self, "can_change_content"):
            content_obj = self.get_content_obj(obj)
            if not self.can_change_content(request, content_obj):
                # Only allow content object fields to be edited if user can change them
                fields += tuple(
                    CONTENT_PREFIX + field
                    for field in self.form._content_fields
                    if field != self._grouper_field_name
                    and field not in self.extra_grouping_fields
                )
        return fields

    def save_model(
        self, request: HttpRequest, obj: models.Model, form: forms.Form, change: bool
    ) -> None:
        """Save/create both grouper and content object"""
        super().save_model(request, obj or form.instance, form, change)
        content_dict = {
            field: form.cleaned_data[CONTENT_PREFIX + field]
            for field in form._content_fields
            if CONTENT_PREFIX + field in form.cleaned_data
        }
        if form._content_instance is None or form._content_instance.pk is None:
            content_dict[self._grouper_field_name] = form.instance
            if hasattr(form._content_model.objects, "with_user"):
                # Create new using with_user syntax if available ...
                form._content_model.objects.with_user(request.user).create(
                    **content_dict
                )
            else:  # pragma: no cover
                # ... without otherwise
                form._content_model.objects.create(**content_dict)
        elif not hasattr(self, "can_change_content") or self.can_change_content(
            request, form._content_instance
        ):
            # Update content instance (only if can_change_content allows it)
            for key, value in content_dict.items():
                setattr(form._content_instance, key, value)
            # Finally force grouper field to point to grouper
            setattr(form._content_instance, self._grouper_field_name, obj)
            form._content_instance.save()


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
        else:
            self._content_instance = None

        # set values for grouping fields
        kwargs["initial"] = {
            **{CONTENT_PREFIX + key: value for key, value in self._admin.current_content_filters.items()},
            **kwargs.get("initial", {}),
        }

        # The actual init
        super().__init__(*args, **kwargs)

        # Hide grouper foreign key
        self.fields[
            CONTENT_PREFIX + self._admin._grouper_field_name
        ].widget = forms.HiddenInput()
        # Will be set on admin model save
        self.fields[CONTENT_PREFIX + self._admin._grouper_field_name].required = False
        self.update_labels(self._content_fields)
        if hasattr(self._admin, "can_change_content") and False:
            if not self._admin.can_change_content(
                self._request, self._content_instance
            ):
                # Only allow content object fields to be edited if user can change them
                for field in self._additional_content_fields:
                    self.fields[field].disabled = True

    def update_labels(self, fields: typing.List[str]) -> None:
        """Adds a language indicator to field labels"""
        if "language" in self._admin.extra_grouping_fields:
            language_dict = get_language_dict()
            language_postfix = f" ({language_dict[self._admin.language]})"
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
                        label_for_field(field, self._admin.content_model)
                        + language_postfix,
                    )

    def clean(self) -> dict:
        if (
            self.cleaned_data.get(CONTENT_PREFIX + "language", None)
            not in get_language_dict()
        ):
            raise ValidationError(
                _(
                    "Invalid language %(value)s. This form cannot be processed. Try changing languages."
                ),
                params=dict(
                    value=self.cleaned_data.get("language", _("<unspecified>"))
                ),
                code="invalid-language",
            )
        return super().clean()


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
        base_fields = {
            CONTENT_PREFIX + key: value for key, value in model_form.base_fields.items()
        }
        return forms.forms.DeclarativeFieldsMetaclass(
            GrouperAdminFormMixin.__name__,
            (_GrouperAdminFormMixin,),
            {
                **base_fields,  # inherit the content model form's fields
                "_content_model": model_form._meta.model,  # remember the model and
                "_content_fields": model_form.base_fields.keys(),  # fields that come from the content form
            },
        )

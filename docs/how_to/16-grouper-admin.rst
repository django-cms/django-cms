.. versionadded:: 4.1

.. _grouper_admin:

How to create an admin class for a grouper model
================================================

What is a grouper model?
------------------------

It's an reusable abstract structural pattern, that is in django CMS used to separate
language independent and language specific content.

django CMS defines grouper-content structure for Page-PageContent as follows:

- The :class:`~cms.models.pagemodel.Page` is the grouper model which represents base
  unit, that can have multiple content objects attached
- The :class:`~cms.models.contentmodels.PageContent` is the content model which
  represents page content that can be different for its grouping field - ``language`` in
  our case. It also includes the placeholders for the frontend editor.

This mechanism ensures that language-independent properties of a page, such as position
in the page tree or permissions, are collected at the grouper model while
language-specific content is collected in the content model.

.. note::

    This pattern is relevant for django CMS Versioning since it versions the content
    objects and not the grouper objects.

    To this end, if you want to create models that should be versionable like the
    :class:`~cms.models.contentmodels.PageContent` of a
    :class:`~cms.models.pagemodel.Page` objects you need to define a grouper and a
    content model.

**Extra grouping fields** define fields of the content model by which they are grouped:
:class:`~cms.models.contentmodels.PageContent` uses ``language`` as an extra grouping
field. This means that one :class:`~cms.models.pagemodel.Page` object can have multiple
:class:`~cms.models.contentmodels.PageContent` objects assign to which differ in their
language.

If not extra grouping fields are given each grouper object can have at most one content
object assigmed to it.

The language field is a typical (but not necessary) extra grouping field.

Administrating grouper models
-----------------------------

To simplify creation of grouper content models, django CMS provides support for both the
model admin class of the grouper model and the change and add forms of the content
model.

In this scenario you will register a model admin for the grouper model and it will
provide the user with the ability to view, change and add content objects, too. You will
not necessarily need to add a model admin class for the content model at all (with the
possible exception of a redirecting stub to allow third party apps to reverse admin
views for the content model, too, see below).

To create a model admin class for a grouper model put the following code in your
`admin.py`:

.. code-block:: python

    from cms.admin.utils import GrouperModelAdmin


    class MyGrouperAdmin(GrouperModelAdmin):
        # Declare content model
        content_model = MyContent
        # Add language tabs to change and add views
        extra_grouping_fields = ("language",)
        # Add grouper and content fields to change list view
        # Add preview and settings action to change list view
        list_display = (
            "field_in_grouper_model",
            "content__field_in_content_model",
            "admin_list_actions",
        )

The property :attr:`~cms.admin.utils.GrouperModelAdmin.content_model` defines which
model is used as the content model. If you do not specify a
:attr:`~cms.admin.utils.GrouperModelAdmin.content_model`, django CMS will look for a
model named like the grouper model but with "Content" appended. The default content
model for ``Post`` would be ``PostContent``.

The content model needs to have a foreign key pointing to the grouper model. The first
foreign key found is assumed to be the field by which the content objects are assigned
to their grouper objects. If you have multiple foreign keys to the grouper model, please
specify :attr:`~cms.admin.utils.GrouperModelAdmin.content_related_field`.

For this example there is only ``language`` as extra grouping field declared. You only
have to proviude tuple of
:attr:`~cms.admin.utils.GrouperModelAdmin.extra_grouping_fields` if you have any.

.. note::

    All fields serving as extra grouping fields must be part of the admin’s fieldsets
    setting for :class:`~cms.admin.utils.GrouperModelAdmin` to work properly. In the
    change form the fields will be invisible.

Change list view
~~~~~~~~~~~~~~~~

For the list display :class:`~cms.admin.utils.GrouperModelAdmin` provides additional
fields from the content model: ``content__{content_model_field_name}``. Those fields can
be used in list_display just as grouper model fields and will automatically show the
content of the currently selected grouping fields.

Finally, :class:`~cms.admin.utils.GrouperModelAdmin` provides two action buttons for
each entry in the change list view:

- to preview the content model in the frontend editor
- to change the settings (i.e., go to the change view of the grouper object)

These are for convenience and appear as soon as ``admin_list_actions`` is added to the
``list_display`` attribute.

Example
~~~~~~~

This is an example (taken from django CMS alias) on how a grouper admin might look like:

.. code-block:: python

    from cms.admin.utils import GrouperModelAdmin


    @admin.register(Alias)
    class AliasAdmin(GrouperModelAdmin):
        list_display = ["content__name", "category", "admin_list_actions"]
        list_display_links = None  # With action buttons a link is not needed
        list_filter = (
            SiteFilter,
            CategoryFilter,
        )  # Custom filters
        fields = (
            "content__name",
            "category",
            "site",
            "content__language",
        )  # feeds into fieldsets
        readonly_fields = ("static_code",)
        form = AliasGrouperAdminForm  # Custom admin form
        extra_grouping_fields = ("language",)  # Language as grouping field
        EMPTY_CONTENT_VALUE = mark_safe(
            _("<i>Missing language</i>")
        )  # Label for missing content objects

Other extra grouping fields (besides language)
----------------------------------------------

The standard templates of django CMS will work with ``language`` as an extra grouping
field out of the box:

- It creates a dropdown to switch languages for the admin's change list view.
- It creates tabs to switch languages for the admin's change and add views.

To use other grouping fields you will have to do two things:

1. You will need to **supply templates** for the change list view and the change and add
   views that render corresponding dropdowns or other ways of selecting which content is
   currently being viewed.
2. You will need to **provide context** for the templates to render the valid choices.

Providing your own templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To show a selector for your additional grouping field you need to overwrite both the
:attr:`~django.contrib.admin.ModelAdmin.change_list_template` and
:attr:`~django.contrib.admin.ModelAdmin.change_form_template`. Your templates can extend
the default templates. Let's say you have "region" as an additional grouping field. For
the **change list template** this might look like this:

.. code-block::

    {% extends "admin/cms/grouper/change_list.html" %}
    {% block language_tabs %}
        {# Here goes the region mark-up #}
        {% if region_dropdown %}
            <div class="region-selector">
                ...
            </div>
        {% endif %}
        {{ block.super }}
    {% endblock %}

For the **change form template** this might look like this:

.. code-block::

    {% extends "admin/cms/grouper/change_form.html" %}
    {% block search %}
        {# Here goes the region mark-up #}
        {% if "region" in cl.model_admin.extra_grouping_fields %}
            <div class="region-selector">
                ...
            </div>
        {% endif %}
        {{ block.super }}
    {% endblock %}

Providing the required context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To provide the required context for your additional grouping model, you will have to
implement two methods in your grouper model admin.

.. code-block:: python

    from cms.admin.utils import GrouperModelAdmin


    class MyGrouperAdmin(GrouperModelAdmin):
        model = MyModel
        extra_grouping_fields = ("region",)

        ...

        def changelist_view(request, extra_context=None):
            """Extra context for changelist_view"""
            my_context = {...}  # Add context on region grouper
            return super().changelist_view(
                request, extra_context={**(extra_context or {}), **my_context}
            )

        def get_extra_context(self, request, obj_id=None):
            """Extra context for add_view and change_view"""
            my_context = {...}  # Add context on region grouper
            return {
                **super().get_extra_context(request, obj_id),
                **my_context,
            }

Consider that the context will require a set of values your additional grouping field
can take. In the region example this might be ``all_regions = {"americas":
_("Americas"), "europe": _("Europe"), ...}``.

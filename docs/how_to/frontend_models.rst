.. _frontend-editable-fields:

###########################################
Frontend editing for Page and Django models
###########################################

.. versionadded:: 3.0

As well as ``PlaceholderFields``, 'ordinary' Django model fields (both on CMS Pages and your own
Django models) can also be edited through django CMS's frontend editing interface. This is very
convenient for the user because it saves having to switch between frontend and admin views.

Using this interface, model instance values that can be edited show the "Double-click to edit"
hint on hover. Double-clicking opens a pop-up window containing the change form for that model.

.. note::

    This interface is not currently available for touch-screen users, but will be improved in
    future releases.

.. warning::

    Template tags used by this feature mark as safe the content of the rendered
    model attribute. This may be a security risk if used on fields which may
    hold non-trusted content. Be aware, and use the template tags accordingly.


.. warning::

    This feature is only partially compatible with django-hvad: using
    ``render_model`` with hvad-translated fields (say
    ``{% render_model object 'translated_field' %}`` returns an error if the
    hvad-enabled object does not exists in the current language.
    As a workaround ``render_model_icon`` can be used instead.

.. _render_model_templatetags:

*************
Template tags
*************

This feature relies on four template tags sharing common code. All require that you ``{% load
cms_tags %}`` in your template:

* :ttag:`render_model` (for editing a specific field)
* :ttag:`render_model_block` (for editing any of the fields in a defined block)
* :ttag:`render_model_icon` (for editing a field represented by another value, such as an image)
* :ttag:`render_model_add` (for adding an instance of the specified model)

Look at the tag-specific page for more detailed reference and discussion of limitations and caveats.

****************
Page titles edit
****************

For CMS pages you can edit the titles from the frontend; according to the
attribute specified a default field, which can also be overridden, will be editable.

Main title::

    {% render_model request.current_page "title" %}


Page title::

    {% render_model request.current_page "page_title" %}

Menu title::

    {% render_model request.current_page "menu_title" %}

All three titles::

    {% render_model request.current_page "titles" %}


You can always customise the editable fields by providing the
`edit_field` parameter::

    {% render_model request.current_page "title" "page_title,menu_title" %}


**************
Page menu edit
**************

By using the special keyword ``changelist`` as edit field the frontend
editing will show the page tree; a common pattern for this is to enable
changes in the menu by wrapping the menu template tags:

.. code-block:: html+django

    {% render_model_block request.current_page "changelist" %}
        <h3>Menu</h3>
        <ul>
            {% show_menu 1 100 0 1 "sidebar_submenu_root.html" %}
        </ul>
    {% endrender_model_block %}

Will render to:

.. code-block:: html+django

    <div class="cms-plugin cms-plugin-cms-page-changelist-1">
        <h3>Menu</h3>
        <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/another">another</a></li>
            [...]
    </div>

.. warning:

    Be aware that depending on the layout of your menu templates, clickable
    area of the menu may completely overlap with the active area of the
    frontend editor thus preventing editing. In this case you may use
    ``{% render_model_icon %}``.
    The same conflict exists when menu template is managed by a plugin.

********************************
Editing 'ordinary' Django models
********************************

As noted above, your own Django models can also present their fields for editing in the frontend.
This is achieved by using the ``FrontendEditableAdminMixin`` base class.

Note that this is only required for fields **other than** ``PlaceholderFields``.
``PlaceholderFields`` are automatically made available for frontend editing.

Configure the model's admin class
=================================

Configure your admin class by adding the ``FrontendEditableAdminMixin`` mixin to it (see
:mod:`Django admin documentation <django.contrib.admin>` for general Django admin information)::

    from cms.admin.placeholderadmin import FrontendEditableAdminMixin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
        ...

The ordering is important: as usual, **mixins must come first**.

Then set up the templates where you want to expose the model for editing, adding a ``render_model``
template tag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" %}</h1>
    {% endblock content %}

See :ttag:`templatetag reference <render_model>` for arguments documentation.


Selected fields edit
====================

Frontend editing is also possible for a set of fields.

Set up the admin
----------------

You need to add to your model admin a tuple of fields editable from the frontend
admin::

    from cms.admin.placeholderadmin import FrontendEditableAdminMixin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
        frontend_editable_fields = ("foo", "bar")
        ...

Set up the template
-------------------

Then add comma separated list of fields (or just the name of one field) to
the template tag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" "some_field,other_field" %}</h1>
    {% endblock content %}



Special attributes
==================

The ``attribute`` argument of the template tag is not required to be a model field,
property or method can also be used as target; in case of a method, it will be
called with request as argument.


.. _custom-views:

Custom views
============

You can link any field to a custom view (not necessarily an admin view) to handle
model-specific editing workflow.

The custom view can be passed either as a named url (``view_url`` parameter)
or as name of a method (or property) on the instance being edited
(``view_method`` parameter).
In case you provide ``view_method`` it will be called whenever the template tag is
evaluated with ``request`` as parameter.

The custom view does not need to obey any specific interface; it will get
``edit_fields`` value as a ``GET`` parameter.

See :ttag:`templatetag reference <render_model>` for arguments documentation.

Example ``view_url``::

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" "some_field,other_field" "" "admin:exampleapp_example1_some_view" %}</h1>
    {% endblock content %}


Example ``view_method``::

    class MyModel(models.Model):
        char = models.CharField(max_length=10)

        def some_method(self, request):
            return "/some/url"


    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "some_attribute" "some_field,other_field" "" "" "some_method" %}</h1>
    {% endblock content %}


Model changelist
================

By using the special keyword ``changelist`` as edit field the frontend
editing will show the model changelist:

.. code-block:: html+django

    {% render_model instance "name" "changelist" %}

Will render to:

.. code-block:: html+django

    <div class="cms-plugin cms-plugin-myapp-mymodel-changelist-1">
        My Model Instance Name
    </div>


.. filters:

*******
Filters
*******

If you need to apply filters to the output value of the template tag, add quoted
sequence of filters as in Django :ttag:`django:filter` template tag:

.. code-block:: html+django

    {% load cms_tags %}

    {% block content %}
    <h1>{% render_model instance "attribute" "" "" "truncatechars:9" %}</h1>
    {% endblock content %}



****************
Context variable
****************

The template tag output can be saved in a context variable for later use, using
the standard `as` syntax:

.. code-block:: html+django

    {% load cms_tags %}

    {% block content %}
    {% render_model instance "attribute" as variable %}

    <h1>{{ variable }}</h1>

    {% endblock content %}


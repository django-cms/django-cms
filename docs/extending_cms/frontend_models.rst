.. _frontend-editable-fields:

###########################################
Frontend editing for Page and Django models
###########################################

.. versionadded:: 3.0

django CMS frontend editing can also be used to edit non-placeholder fields from
the frontend, both for pages and your standard Django models.

By enabling it, it's possible to double click on a value of a model instance in
the frontend and access the instance changeform in a popup window, like the page
changeform.


.. warning::

    ``show_editable_model`` marks as safe the content of the rendered model
    attribute. This may be a security risk if used on fields which may hold
    non-trusted content. Be aware, and use the templatetag accordingly.

****************
Page titles edit
****************

For CMS pages you can edit the titles from the frontend; according to the
attribute specified a overridable default field will be editable.

Main title::

    {% show_editable_model request.current_page "title" %}


Page title::

    {% show_editable_model request.current_page "page_title" %}

Menu title::

    {% show_editable_model request.current_page "menu_title" %}

All three titles::

    {% show_editable_model request.current_page "titles" %}


You can always customize the editable fields by providing the
`edit_field` parameter::

    {% show_editable_model request.current_page "title" "page_title,menu_title" %}



******************
Django models edit
******************

For Django models you can further customize what's editable on the frontend
and the resulting forms.

Complete changeform edit
========================

You need to properly setup your admin class by adding the
``FrontendEditableAdmin`` mixin to the parents of your admin class (see
:mod:`Django admin documentation <django.contrib.admin>` for further information)
on Django admin::

    from cms.admin.placeholderadmin import FrontendEditableAdmin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdmin, admin.ModelAdmin):
        ...

Then setup the templates adding ``show_editable_model`` templatetag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" %}</h1>
    {% endblock content %}

See :ttag:`templatetag reference <show_editable_model>` for arguments documentation.


Selected fields edit
====================

Frontend editing is also possible for a set of fields.

Set up the admin
----------------

You need to add to your model admin a tuple of fields editable from the frontend
admin::

    from cms.admin.placeholderadmin import FrontendEditableAdmin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdmin, admin.ModelAdmin):
        frontend_editable_fields = ("foo", "bar")
        ...

Set up the template
-------------------

Then add comma separated list of fields (or just the name of one field) to
the templatetag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" "some_field,other_field" %}</h1>
    {% endblock content %}



Special attributes
==================

The ``attribute`` argument of the templatetag is not required to be a model field,
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
In case you provide ``view_method`` it will be called whenever the templatetag is
evaluated with ``request`` as parameter.

The custom view does not need to obey any specific interface; it will get
``edit_fields`` value as a ``GET`` parameter.

See :ttag:`templatetag reference <show_editable_model>` for arguments documentation.

Example ``view_url``::

    {% load cms_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" "some_field,other_field" "" "admin:exampleapp_example1_some_view" %}</h1>
    {% endblock content %}


Example ``view_method``::
    
    class MyModel(models.Model):
        char = models.CharField(max_length=10)
        
        def some_method(self, request):
            return "/some/url"
    

    {% load cms_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" "some_field,other_field" "" "" "some_method" %}</h1>
    {% endblock content %}


.. filters:

*******
Filters
*******

If you need to apply filters to the output value of the templatetag, add quoted
sequence of filters as in Django :ttag:`django:filter` templatetag::

    {% load cms_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "attribute" "" "" "truncatechars:9" %}</h1>
    {% endblock content %}


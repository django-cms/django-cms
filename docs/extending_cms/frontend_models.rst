.. _frontend-editable-fields:

##################################
Frontend editing for Django models
##################################

.. versionadded:: 3.0

django CMS frontend editing can also be used for your standard Django models.

By enabling it, it's possible to double click on a value of a model instance in
the frontend and access the instance changeform in a popup window, like the page
changeform.

************************
Complete changeform edit
************************

You need to properly setup your admin class by adding the
``FrontendEditableAdmin`` mixin to the parents of your admin class (see
:mod:`Django admin documentation <django.contrib.admin>` for further information)
on Django admin::

    from cms.admin.placeholderadmin import FrontendEditableAdmin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdmin, admin.ModelAdmin):
        ...

Then setup the templates adding ``show_editable_model`` templatetag::

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" %}</h1>
    {% endblock content %}

See `templatetag reference <show_editable_model_reference>`_ for arguments documentation.

********************
Selected fields edit
********************

Frontend editing is also possible for a set of fields.

Set up the admin
================

You need to add to your model admin a tuple of fields editable from the frontend
admin::

    from cms.admin.placeholderadmin import FrontendEditableAdmin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdmin, admin.ModelAdmin):
        frontend_editable_fields = ("foo", "bar")
        ...

Set up the template
===================

Then add comma separated list of fields (or just the name of one field) to
the templatetag::

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" "some_field,other_field" %}</h1>
    {% endblock content %}



******************
Special attributes
******************

The ``attribute`` argument of the templatetag is not required to be a model field,
property or method can also be used as target; in case of a method, it will be
called with request as argument.

.. _custom-views:

************
Custom views
************

You can link any field to a custom view (not necessarily an admin view) to handle
model-specific editing workflow.

The custom view can be passed either as a named url (``view_url`` parameter)
or as name of a method (or property) on the instance being edited
(``view_method`` parameter).
In case you provide ``view_method`` it will be called whenever the templatetag is
evaluated with ``request`` as parameter.

The custom view does not need to obey any specific interface; it will get
``edit_fields`` value as a ``GET`` parameter.

See `templatetag reference <show_editable_model_reference>`_ for arguments documentation.

Example ``view_url``::

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" "some_field,other_field" "" "admin:exampleapp_example1_some_view" %}</h1>
    {% endblock content %}


Example ``view_method``::
    
    class MyModel(models.Model):
        char = models.CharField(max_length=10)
        
        def some_method(self, request):
            return "/some/url"
    

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" "some_field,other_field" "" "" "some_method" %}</h1>
    {% endblock content %}

.. _show_editable_model_reference:

*********************
templatetag reference
*********************

``show_editable_model`` works by showing the content of the given attribute in
the model instance.

If the toolbar is not enabled, the value of the attribute is rendered in the
template without further action.

If the toolbar is enabled, frontend code is added to make the attribute value
clickable.

Arguments:

* ``instance``: instance of your model in the template
* ``attribute``: the name of the attribute you want to show in the template; it
  can be a context variable name; it's possible to target field, property or
  callable for the specified model;
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor;
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.
* ``view_url`` (optional): the name of a url that will be reversed using the
  instance ``pk`` and the ``language`` as arguments;
* ``view_method`` (optional): a method name that will return a URL to a view;
  the method must accept ``request`` as first parameter.


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad

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

After creating the admin class for the model (see
:mod:`Django admin documentation <django.contrib.admin>`), you just have to set
up the your model's template.

Set up the template
===================

Add ``show_editable_model``:

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" %}</h1>
    {% endblock content %}

See `templatetag reference <show_editable_model_reference>`_ for description of arguments.

********************
Selected fields edit
********************

Frontend editing is also possible for a restricted set of fields, although not
as automatic as the example above.

Set up the admin
================

First you need to properly setup your admin class by adding the
``FrontendEditableAdmin`` mixin to the parents of your admin class and declaring
a tuple of fields editable from the frontend admin

    from cms.admin.placeholderadmin import FrontendEditableAdmin
    from django.contrib import admin


    class MyModelAdmin(FrontendEditableAdmin, admin.ModelAdmin):
        frontend_editable_fields = ("foo", "bar")
        ...

Set up the template
===================

If you only want to edit the fields to be rendered in the page just add
``show_editable_model`` to your template:

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_field" "admin:exampleapp_example1_edit_field" %}</h1>
    {% endblock content %}

The ``admin:exampleapp_example1_edit_field`` string must be changed according
to your application and model names (e.g.: is the application is named ``news``
and the model is called ``NewsModel`` you'd write the string
``admin:news_newsmodel_edit_field``).
The ``edit_field`` is provided by ``FrontendEditableAdmin`` mixin, so you're not
required to write your own admin view (but you can do that, if you want, see
`Custom views <custom-views>`_).

Edit multiple fields
====================

If you want to edit multiple fields at once use the templatetag ``edit_fields``
attribute:

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_field" "admin:exampleapp_example1_edit_field" "char_1,char_2" %}</h1>
    {% endblock content %}



******************
Special attributes
******************

The ``attribute`` argument of the templatetag is not required to be a field of
the model, you can also use a property or a method as a target.

If you use property or method and link it to single field edit, you **must**
provide the ``edit_fields`` argument to target a specific field to edit.

.. _custom-views:

************
Custom views
************

You can link any field to a custom view (not necessarily an admin view); in any
case your view does not need to obey any specific interface, other than
possibly check to ``_popup`` query string parameter to select a popup-enabled
template.

Custom views can be specified by either passing the ``view_url`` attribute
(which will be passed to the ``reverse`` function with the instance ``pk`` and
``attribute_name`` parameters) or by using the ``view_method`` to pass a
method (or property) of the model instance; this property / method must return
a complete URL.

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
* ``view_url`` (optional): the name of a url that will be reversed using the
  instance ``pk`` and the ``attribute`` (or ``edit_field``) as arguments;
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor;
* ``view_method`` (optional): a method name that will return a URL to a view;
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad
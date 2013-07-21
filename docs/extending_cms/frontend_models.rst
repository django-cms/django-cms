##################################
Frontend editing for Django models
##################################

.. versionadded:: 3.0

django CMS frontend editing can also be used for your standard Django models.

By enabling it, it's possible to double click on a value of a model instance in
the frontend and access the instance changeform in a popup window, like the page
changeform.

*************
How to enable
*************

To enable frontend edit for you Django models add the ``show_editable_model``
templatetag in your model's template::

    {% load placeholder_tags %}

    {% block content %}
    <h1>{% show_editable_model instance "some_attribute" %}</h1>

***********
templatetag
***********

``show_editable_model`` works by showing the content of the given attribute in
the model instance.

If the toolbar is not enable, the value of the attribute is rendered in the
template without further action.

If the toolbar is enabled, frontend code is added to make the attribute value
clickable.

Arguments:

* ``instance``: instance of your model in the template
* ``attribute``: the name of the attribute you want to show in the template; it
  can be a context variable name; it's possible to target field, property or
  callable.
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad
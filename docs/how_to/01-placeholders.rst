.. _placeholders_outside_cms:

How to use placeholders outside the CMS
=======================================

Placeholder fields are special model fields that django CMS uses to render user-editable
content (plugins) in templates. That is, it's the place where a user can add text, video
or any other plugin to a webpage, using the same frontend editing as the CMS pages.

.. versionchanged:: 4.0

    Since django CMS 4.0 the toolbar offers preview and edit endpoints for Django models
    which contain Placeholders.

    - This allows for models (such as django CMS Alias) which do not have a user-facing
      view to still contain placeholders.
    - However, it requires the registration of frontend-editable models with django
      CMS.
    - Also, views need to tell the toolbar if they contain a frontend-editable model.

Placeholders can be viewed as containers for :class:`~cms.models.pluginmodel.CMSPlugin`
instances, and can be used outside the CMS in custom applications using the
:class:`~cms.models.fields.PlaceholderRelationField`.

By defining a :class:`~cms.models.fields.PlaceholderRelationField` on a custom model you
can take advantage of the full power of :class:`~cms.models.pluginmodel.CMSPlugin` in
one or more placeholders.

.. warning::

    Django CMS 3.x used a different way of integrating placeholders. It's
    ``PlaceholderField("slot_name")`` needs to be changed into a
    ``PlaceholderRelationField`` (available since django CMS 4.x).

Get started
-----------

You need to define a :class:`~cms.models.fields.PlaceholderRelationField` on the model
you would like to use:

.. code-block::

    from django.db import models
    from cms.models.fields import PlaceholderRelationField
    from cms.utils.placeholder import get_placeholder_from_slot

    class MyModel(models.Model):
        # your fields
        placeholders = PlaceholderRelationField()

        @cached_property
        def my_placeholder(self):
            return get_placeholder_from_slot(self.placeholders, "slot_name")

        # your methods

The :class:`~cms.models.fields.PlaceholderRelationField` can reference more than one
field. It is customary to add (cached) properties to the model referring to specific
placeholders. The utility function
:func:`~cms.utils.placeholder.get_placeholder_from_slot` retrieves a placeholder object
based on its slot name.

The ``slot`` is used in templates, to determine where the placeholder's plugins should
appear in the page, and in the placeholder configuration :setting:`CMS_PLACEHOLDER_CONF`,
which determines which plugins may be inserted into this placeholder.

.. note::

    If you add a PlaceholderRelationField to an existing model, you'll be able to see
    the placeholder in the frontend editor only after saving the relevant instance.

Admin Integration
~~~~~~~~~~~~~~~~~

.. versionchanged:: 4.0

Since django CMS version 4 :class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` is
not required any more. For now, it still exists as an empty mixin but will be removed in
a future version.

I18N Placeholders
~~~~~~~~~~~~~~~~~

Placeholders and plugins within them support multiple languages out of the box.

If you need other fields translated as well, django CMS has support for django-hvad_. If
you use a ``TranslatableModel`` model be sure to **not** include the placeholder fields
amongst the translated fields:

.. code-block::

    class MultilingualExample1(TranslatableModel):
        translations = TranslatedFields(
            title=models.CharField('title', max_length=255),
            description=models.CharField('description', max_length=255),
        )
        placeholders = PlaceholderRelationField()

        @cached_property
        def my_placeholder(self):
            return get_placeholder_from_slot(self.placeholders, "slot_name")

        def __str__(self):
            return self.title

Templates
~~~~~~~~~

To render the placeholder in a template you use the :ttag:`render_placeholder` tag from
the :mod:`~cms.templatetags.cms_tags` template tag library:

.. code-block:: html+django

    {% load cms_tags %}

    {% render_placeholder mymodel_instance.my_placeholder "640" %}

The :ttag:`render_placeholder` tag takes the following parameters:

- :class:`~cms.models.fields.PlaceholderField` instance
- ``width`` parameter for context sensitive plugins (optional)
- ``language`` keyword plus ``language-code`` string to render content in the specified
  language (optional)

The view in which you render your placeholder field must return the :class:`request
<django.http.HttpRequest>` object in the context. The frontend editing and preview
endpoints require a view to render an object. This method takes the request and the
object as parameter (see example below: ``render_my_model``).

If the object has a user-facing view it typically is identical to the preview and
editing endpoints, but has to get the object from the URL (e.g., by its primary key).
**It also needs to set the toolbar object, so that the toolbar will have Edit and
Preview buttons:**

.. code-block:: python

    from django.shortcuts import get_object_or_404, render


    def render_my_model(request, obj):
        return render(
            request,
            "my_model_detail.html",
            {
                "object": obj,
            },
        )


    def my_model_detail(request, id):
        obj = get_object_or_404(MyModel, id=id)  # Get the object (here by id)
        request.toolbar.set_object(obj)  # Announce the object to the toolbar
        return render_my_model(request, obj)  # Same as preview rendering

.. note::

    If you want to render plugins from a specific language, you can use the tag like
    this:

    .. code-block:: html+django

        {% load cms_tags %}

        {% render_placeholder mymodel_instance.my_placeholder language 'en' %}

Adding the slots to the model
-----------------------------

To let django CMS' frontend editor know which placeholders the model contains, declare them in
a second template, only needed for rendering the structure mode, called, say,
``templtes/my_app/my_model_structure.html``:

.. code-block:: html+django

    {% load cms_tags %}
    {% placeholder "slot_name" %}

The important bit is to include all slot names for the model in the structure template.
Other parts of the templte are not necessary.

Add the structure mode template to the model
--------------------------------------------

Let the model know about this template by declaring the ``get_template()`` method:

.. code-block::

    class MyModel(models.Model):
        ...

        def get_template(self):
            return "my_app/my_model_structure.html"

        ...

Registering the model for frontend editing
------------------------------------------

.. versionadded:: 4.0

The final step is to register the model for frontend editing. Since django CMS 4 this is
done by adding a :class:`~cms.app_base.CMSAppConfig` class to the app's `cms_config.py`
file:

.. code-block::

    from cms.app_base import CMSAppConfig
    from . import models, views


    class MyAppConfig(CMSAppConfig):
        cms_enabled = True
        cms_toolbar_enabled_models = [(models.MyModel, views.render_my_model)]

Adding content to a placeholder
-------------------------------

Placeholders can be edited from the frontend by visiting the page displaying your model
(where you put the :ttag:`render_placeholder` tag), then appending ``?toolbar_on`` to the
page's URL.

This will make the frontend editor top banner appear (and if necessary will require you
to login).

Once in frontend editing mode, the interface for your application's
``PlaceholderFields`` will work in much the same way as it does for CMS Pages, with a
switch for Structure and Content modes and so on.

.. _placeholder_object_permissions:

Permissions
~~~~~~~~~~~

To be able to edit a placeholder user must be a ``staff`` member and needs either edit
permissions on the model that contains the
:class:`~cms.models.fields.PlaceholderRelationField`, or permissions for that specific
instance of that model. Required permissions for edit actions are:

- to ``add``: require ``add`` **or** ``change`` permission on related Model or instance.
- to ``change``: require ``add`` **or** ``change`` permission on related Model or
  instance.
- to ``delete``: require ``add`` **or** ``change`` **or** ``delete`` permission on
  related Model or instance.

With this logic, an user who can ``change`` a Model's instance but can not ``add`` a new
Model's instance will be able to add some placeholders or plugins to existing Model's
instances.

Model permissions are usually added through the default Django ``auth`` application and
its admin interface. Object-level permission can be handled by writing a custom
authentication backend as described in `django docs
<https://docs.djangoproject.com/en/stable/topics/auth/customizing/#handling-object-permissions>`_

For example, if there is a ``UserProfile`` model that contains a
``PlaceholderRelationField`` then the custom backend can refer to a ``has_perm`` method
(on the model) that grants all rights to current user only based on the user's
``UserProfile`` object:

.. code-block::

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_staff:
            return False
        if isinstance(obj, UserProfile):
            if user_obj.get_profile()==obj:
                return True
        return False

.. _django-hvad: https://github.com/kristianoellegaard/django-hvad

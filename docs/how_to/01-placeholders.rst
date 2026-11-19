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

Two ways to render model placeholders
-------------------------------------

A quick glossary:

- A **slot** is the string name that identifies a placeholder in a template
  (for example ``"content"``). Slot names are also used by :setting:`CMS_PLACEHOLDER_CONF`
  to configure which plugins can be inserted.
- A **placeholder** is the per-instance container (a
  :class:`~cms.models.placeholdermodel.Placeholder` object) that holds the plugins for a
  given slot on a given model instance.
- The **structure board** is django CMS's frontend editor view where editors add, remove
  and reorder plugins.

django CMS offers two template tags for placeholders on your own models:

- :ttag:`placeholder` — *declares and renders* in one step. The same template is both what
  your view renders and what django CMS scans to discover slot names for the structure
  board.
- :ttag:`render_placeholder` — *only renders* a placeholder instance that the model exposes
  as a property (typically via :func:`~cms.utils.placeholder.get_placeholder_from_slot`).
  Because this tag does not declare its slot, the model also needs a separate
  declaration-only template for the structure board to discover the slots.

**Prefer Approach 1 for new models.** Use Approach 2 only when you're integrating with
code that already uses :ttag:`render_placeholder`, or when you want each placeholder
exposed as a named model property.

Both approaches share the same :class:`~cms.models.fields.PlaceholderRelationField` and the
toolbar integration described in :ref:`toolbar_object` below.


Approach 1: Using ``{% placeholder %}``
---------------------------------------

Step 1 — Add a :class:`~cms.models.fields.PlaceholderRelationField` and a
``get_template()`` method pointing to the template you'll create in Step 2. This is the
template your view will render and that django CMS will scan for slot declarations:

.. code-block:: python

    from django.db import models
    from cms.models.fields import PlaceholderRelationField

    class MyModel(models.Model):
        # your fields
        placeholders = PlaceholderRelationField()

        def get_template(self):
            return "my_app/my_model_template.html"

Step 2 — Create that template. It declares the slots your model owns with the
:ttag:`placeholder` tag, alongside any other markup you need — the same tags are used both
to declare the slots (so django CMS can list them in the structure board) and to render
their content:

.. code-block:: html+django

    {# templates/my_app/my_model_template.html #}
    {% load cms_tags %}
    <h1>{{ object.title }}</h1>
    <main>
        {% placeholder "content" %}
    </main>
    <aside>
        {% placeholder "sidebar" %}
    </aside>

Step 3 — In your view, register the model instance on the toolbar (see
:ref:`toolbar_object`) and render the same template. Setting the toolbar object is what
tells the :ttag:`placeholder` tag which object's placeholders to resolve against:

.. code-block:: python

    from django.shortcuts import get_object_or_404, render

    def my_model_detail(request, id):
        obj = get_object_or_404(MyModel, id=id)
        request.toolbar.set_object(obj)
        return render(request, "my_app/my_model_template.html", {"object": obj})

Load the view with the frontend editor active to add plugins to each slot — see
*Adding content to a placeholder* below.


Approach 2: Using ``{% render_placeholder %}``
----------------------------------------------

In this approach the model exposes a :class:`~cms.models.placeholdermodel.Placeholder`
instance per slot, and the user-facing template passes that instance to
:ttag:`render_placeholder`. Because :ttag:`render_placeholder` does not declare its slot,
the model also needs a **separate declaration-only template**. Unlike Approach 1, the
template registered with ``get_template()`` is *not* the one your view renders.

Step 1 — Add the :class:`~cms.models.fields.PlaceholderRelationField`, a cached-property
accessor for each slot, and a ``get_template()`` pointing to the declaration-only template
you'll create in Step 2:

.. code-block:: python

    from django.db import models
    from django.utils.functional import cached_property
    from cms.models.fields import PlaceholderRelationField
    from cms.utils.placeholder import get_placeholder_from_slot

    class MyModel(models.Model):
        # your fields
        placeholders = PlaceholderRelationField()

        def get_template(self):
            return "my_app/my_model_structure.html"

        @cached_property
        def content_placeholder(self):
            return get_placeholder_from_slot(self.placeholders, "content")

        @cached_property
        def sidebar_placeholder(self):
            return get_placeholder_from_slot(self.placeholders, "sidebar")

:func:`~cms.utils.placeholder.get_placeholder_from_slot` retrieves — or, if needed,
creates — the placeholder object for the given slot name. Add one cached property per slot.

Step 2 — Create the declaration-only template. This file is never rendered to the visitor;
django CMS only scans it for :ttag:`placeholder` tags to discover which slots the model
owns. Other markup in it is ignored:

.. code-block:: html+django

    {# templates/my_app/my_model_structure.html #}
    {% load cms_tags %}
    {% placeholder "content" %}
    {% placeholder "sidebar" %}

Step 3 — Create the user-facing template. Pass each placeholder instance from Step 1 to
:ttag:`render_placeholder`:

.. code-block:: html+django

    {# templates/my_app/my_model_template.html #}
    {% load cms_tags %}
    <h1>{{ object.title }}</h1>
    <main>
        {% render_placeholder object.content_placeholder %}
    </main>
    <aside>
        {% render_placeholder object.sidebar_placeholder %}
    </aside>

See :ttag:`render_placeholder` for optional parameters (``width``, ``language``, ``as``).

Step 4 — In your view, register the model instance on the toolbar (see
:ref:`toolbar_object`) and render the user-facing template:

.. code-block:: python

    from django.shortcuts import get_object_or_404, render

    def my_model_detail(request, id):
        obj = get_object_or_404(MyModel, id=id)
        request.toolbar.set_object(obj)
        return render(request, "my_app/my_model_template.html", {"object": obj})

Load the view with the frontend editor active to add plugins to each slot — see
*Adding content to a placeholder* below.


.. _toolbar_object:

Setting and getting the placeholder-enabled object from the toolbar
-------------------------------------------------------------------

The toolbar provides two methods for managing the object associated with placeholder
editing. These are essential for enabling the toolbar's Edit and Preview buttons, and — in
Approach 1 — for resolving :ttag:`placeholder` tags against your model.

**set_object(obj)**
    Associates a Django model instance with the toolbar. This method only sets the object if
    one hasn't already been set. The object is typically a model instance that contains
    placeholders, such as a :class:`~cms.models.contentmodels.PageContent` object or any
    other model that supports editable placeholders through a
    :class:`~cms.models.fields.PlaceholderRelationField`.

    The associated object is used by other toolbar methods to generate appropriate URLs for
    editing, preview, and structure modes.

**get_object()**
    Returns the object currently associated with the toolbar, or ``None`` if no object has
    been set. This method can be used to retrieve the object that was previously set using
    ``set_object()``.

Usage in Views
~~~~~~~~~~~~~~

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

You can also retrieve the object from the toolbar in your views using the ``get_object()`` method:

.. code-block:: python

    def my_view(request):
        my_content = request.toolbar.get_object()  # Can be anything: PageContent, PostContent, AliasContent, etc.
        if my_content:
            my_post = my_content.post  # only works for PostContent, of course
        # ... rest of your view logic

.. note::

    If using class based views, you can set the toolbar object in the ``get_context_data``
    method of your view and add a stub view usable when you
    :ref:`register the model for frontend editing <register_model_frontend_editing>`.

    .. code-block:: python

        from django.views.generic.detail import DetailView

        class MyModelDetailView(DetailView):
            # your detail view attributes

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                self.request.toolbar.set_object(self.object)
                return context

        def my_model_endpoint_view(request, my_model):
            return MyModelDetailView.as_view()(request, pk=my_model.pk)

Usage in Templates
~~~~~~~~~~~~~~~~~~

You can also access the toolbar object directly in templates:

.. code-block:: html+django

    {# Access the object directly #}
    {{ request.toolbar.get_object.title }}

    {# Use with template tag for more complex operations #}
    {% with my_obj=request.toolbar.get_object %}
        {% if my_obj %}
            <h2>{{ my_obj.title }}</h2>
            <p><strong>{{ my_obj.description }}</strong></p>
        {% endif %}
    {% endwith %}

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

.. _register_model_frontend_editing:

Registering the model for frontend editing
------------------------------------------

.. versionadded:: 4.0

The final step is to register the model for frontend editing. Since django CMS 4 this is
done by adding a :class:`~cms.app_base.CMSAppConfig` class to the app's `cms_config.py`
file:

.. code-block:: python

    from cms.app_base import CMSAppConfig
    from . import models, views


    class MyAppConfig(CMSAppConfig):
        cms_enabled = True
        cms_toolbar_enabled_models = [(models.MyModel, views.render_my_model)]

.. note::

    If using class based views, use the stub view in ``cms_toolbar_enabled_models`` attribute.

    .. code-block:: python

        cms_toolbar_enabled_models = [(models.MyModel, views.my_model_endpoint_view)]


Adding content to a placeholder
-------------------------------

Placeholders can be edited from the frontend by visiting the page displaying your model
(where you put the :ttag:`placeholder` or :ttag:`render_placeholder` tag), then appending
``?toolbar_on`` to the page's URL.

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

.. _django-parler: https://github.com/django-parler/django-parler

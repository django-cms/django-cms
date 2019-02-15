.. _placeholders_outside_cms:

#######################################
How to use placeholders outside the CMS
#######################################

Placeholders are special model fields that django CMS uses to render
user-editable content (plugins) in templates. That is, it's the place where a
user can add text, video or any other plugin to a webpage, using the same
frontend editing as the CMS pages.

Placeholders can be viewed as containers for :class:`~cms.models.pluginmodel.CMSPlugin` instances, and
can be used outside the CMS in custom applications using the
:class:`~cms.models.fields.PlaceholderField`.

By defining one (or several) :class:`~cms.models.fields.PlaceholderField` on a
custom model you can take advantage of the full power of :class:`~cms.models.pluginmodel.CMSPlugin`.

***********
Get started
***********

You need to define a :class:`~cms.models.fields.PlaceholderField` on the model you would like to
use::

    from django.db import models
    from cms.models.fields import PlaceholderField

    class MyModel(models.Model):
        # your fields
        my_placeholder = PlaceholderField('placeholder_name')
        # your methods


The :class:`~cms.models.fields.PlaceholderField` has one required parameter, a string ``slotname``.

The ``slotname`` is used in templates, to determine where the placeholder's plugins should appear
in the page, and in the placeholder configuration :setting:`CMS_PLACEHOLDER_CONF`, which determines
which plugins may be inserted into this placeholder.

You can also use a callable for the ``slotname``, as in::

    from django.db import models
    from cms.models.fields import PlaceholderField

    def my_placeholder_slotname(instance):
        return 'placeholder_name'

    class MyModel(models.Model):
        # your fields
        my_placeholder = PlaceholderField(my_placeholder_slotname)
        # your methods

.. warning::

    For security reasons the related_name for a
    :class:`~cms.models.fields.PlaceholderField` may not be suppressed using
    ``'+'``; this allows the cms to check permissions properly. Attempting to do
    so will raise a :exc:`ValueError`.

.. note::

    If you add a PlaceholderField to an existing model, you'll be able to see
    the placeholder in the frontend editor only after saving the relevant instance.

Admin Integration
=================

.. versionchanged:: 3.0

Your model with ``PlaceholderFields`` can still be edited in the admin. However, any
PlaceholderFields in it will **only be available for editing from the frontend**.
``PlaceholderFields`` **must** not be present in any ``fieldsets``, ``fields``, ``form`` or other
``ModelAdmin`` field's definition attribute.

To provide admin support for a model with a ``PlaceholderField`` in your application's admin, you
need to use the mixin :class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` along with the
:class:`~django.contrib.admin.ModelAdmin`. Note that the ``PlaceholderAdminMixin`` **must** precede
the ``ModelAdmin`` in the class definition::

    from django.contrib import admin
    from cms.admin.placeholderadmin import PlaceholderAdminMixin
    from myapp.models import MyModel

    class MyModelAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
        pass

    admin.site.register(MyModel, MyModelAdmin)

I18N Placeholders
=================

Out of the box :class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` supports multiple
languages and will display language tabs. If you extend your model admin class derived from
``PlaceholderAdminMixin`` and overwrite ``change_form_template`` have a look at
``admin/placeholders/placeholder/change_form.html`` to see how to display the language tabs.

If you need other fields translated as well, django CMS has support for `django-hvad`_. If you use
a ``TranslatableModel`` model be sure to **not** include the placeholder fields amongst the
translated fields::

    class MultilingualExample1(TranslatableModel):
        translations = TranslatedFields(
            title=models.CharField('title', max_length=255),
            description=models.CharField('description', max_length=255),
        )
        placeholder_1 = PlaceholderField('placeholder_1')

        def __unicode__(self):
            return self.title

Be sure to combine both hvad's ``TranslatableAdmin`` and :class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` when
registering your model with the admin site::

    from cms.admin.placeholderadmin import PlaceholderAdminMixin
    from django.contrib import admin
    from hvad.admin import TranslatableAdmin
    from myapp.models import MultilingualExample1

    class MultilingualModelAdmin(TranslatableAdmin, PlaceholderAdminMixin, admin.ModelAdmin):
        pass

    admin.site.register(MultilingualExample1, MultilingualModelAdmin)

Templates
=========

To render the placeholder in a template you use the :ttag:`render_placeholder` tag from the
:mod:`~cms.templatetags.cms_tags` template tag library:

.. code-block:: html+django

    {% load cms_tags %}

    {% render_placeholder mymodel_instance.my_placeholder "640" %}

The :ttag:`render_placeholder` tag takes the following parameters:

* :class:`~cms.models.fields.PlaceholderField` instance
* ``width`` parameter for context sensitive plugins (optional)
* ``language`` keyword plus ``language-code`` string to render content in the
  specified language (optional)

The view in which you render your placeholder field must return the
:class:`request <django.http.HttpRequest>` object in the context. This is
typically achieved in Django applications by using :class:`~django.template.RequestContext`::

    from django.shortcuts import get_object_or_404, render

    def my_model_detail(request, id):
        object = get_object_or_404(MyModel, id=id)
        return render(request, 'my_model_detail.html', {
            'object': object,
        })

If you want to render plugins from a specific language, you can use the tag
like this:

.. code-block:: html+django

    {% load cms_tags %}

    {% render_placeholder mymodel_instance.my_placeholder language 'en' %}

*******************************
Adding content to a placeholder
*******************************

.. versionchanged:: 3.0

Placeholders can be edited from the frontend by visiting the page displaying your model (where you
put the :ttag:`render_placeholder` tag), then appending ``?edit`` to the page's URL.

This will make the frontend editor top banner appear (and if necessary will require you to login).

Once in frontend editing mode, the interface for your application's ``PlaceholderFields`` will work
in much the same way as it does for CMS Pages, with a switch for Structure and Content modes and so
on.

There is no automatic draft/live functionality for general Django models, so content is updated
instantly whenever you add/edit them.

Options
=======

If you need to change ``?edit`` to a custom string (say, ``?admin_on``) you may
set ``CMS_TOOLBAR_URL__EDIT_ON`` variable in your ``settings.py`` to
``"admin_on"``.

You may also change other URLs with similar settings:

* ``?edit_off`` (``CMS_TOOLBAR_URL__EDIT_OFF``)
* ``?build`` (``CMS_TOOLBAR_URL__BUILD``)
* ``?toolbar_off`` (``CMS_TOOLBAR_URL__DISABLE``)

When changing these settings, please be careful because you might inadvertently replace reserved
strings in system (such as ``?page``). We recommended you use safely unique strings for this option
(such as ``secret_admin`` or ``company_name``).

.. _placeholder_object_permissions:

Permissions
===========

To be able to edit a placeholder user must be a ``staff`` member and needs either edit permissions
on the model that contains the :class:`~cms.models.fields.PlaceholderField`, or permissions for
that specific instance of that model. Required permissions for edit actions are:

* to ``add``: require ``add`` **or** ``change`` permission on related Model or instance.
* to ``change``: require ``add`` **or** ``change`` permission on related Model or instance.
* to ``delete``: require ``add`` **or** ``change`` **or** ``delete`` permission on related Model
  or instance.

With this logic, an user who can ``change`` a Model's instance but can not ``add`` a new
Model's instance will be able to add some placeholders or plugins to existing Model's instances.

Model permissions are usually added through the default Django ``auth`` application and its admin
interface. Object-level permission can be handled by writing a custom authentication backend as
described in `django docs
<https://docs.djangoproject.com/en/stable/topics/auth/customizing/#handling-object-permissions>`_

For example, if there is a ``UserProfile`` model that contains a ``PlaceholderField`` then the
custom backend can refer to a ``has_perm`` method (on the model) that grants all rights to current
user only based on the user's ``UserProfile`` object::

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_staff:
            return False
        if isinstance(obj, UserProfile):
            if user_obj.get_profile()==obj:
                return True
        return False


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad

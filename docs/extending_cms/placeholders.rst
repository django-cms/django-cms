############################
Placeholders outside the CMS
############################

Placeholders are special model fields that django CMS uses to render
user-editable content (plugins) in templates. That is, it's the place where a
user can add text, video or any other plugin to a webpage, using either the
normal Django admin interface or the so called `frontend editing`.

Placeholders can be viewed as containers for :class:`CMSPlugin` instances, and
can be used outside the CMS in custom applications using the
:class:`~cms.models.fields.PlaceholderField`.

By defining one (or several) :class:`~cms.models.fields.PlaceholderField` on a custom model you can take
advantage of the full power of :class:`CMSPlugin`, including frontend editing.


**********
Quickstart
**********

You need to define a :class:`~cms.models.fields.PlaceholderField` on the model you would like to
use::

    from django.db import models
    from cms.models.fields import PlaceholderField

    class MyModel(models.Model):
        # your fields
        my_placeholder = PlaceholderField('placeholder_name')
        # your methods


The :class:`~cms.models.fields.PlaceholderField` has one required parameter (`slotname`) which can be a of type string, allowing you to configure which plugins can be used in this
placeholder (configuration is the same as for placeholders in the CMS) or you can also provide a callable like so::

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
    :class:`~cms.models.fields.PlaceholderField` may not be surpressed using
    ``'+'`` to allow the cms to check permissions properly. Attempting to do
    so will raise a :exc:`ValueError`.


Admin Integration
=================

If you install this model in the admin application, you have to use
:class:`~cms.admin.placeholderadmin.PlaceholderAdmin` instead of
:class:`~django.contrib.admin.ModelAdmin` so the interface renders
correctly::

    from django.contrib import admin
    from cms.admin.placeholderadmin import PlaceholderAdmin
    from myapp.models import MyModel

    admin.site.register(MyModel, PlaceholderAdmin)


I18N Placeholders
=================

Out of the box :class:`~cms.admin.placeholderadmin.PlaceholderAdmin` supports multiple languages and will
display language tabs. If you extend `PlaceholderAdmin` and overwrite `change_form_template` be sure to have a look at
'admin/placeholders/placeholder/change_form.html' on how to display the language tabs.

If you need other fields then the placeholders translated as well: django CMS has support for `django-hvad`_. If you
use a `TranslatableModel` model be sure to not include the placeholder fields in the translated fields::

    class MultilingualExample1(TranslatableModel):
        translations = TranslatedFields(
            title=models.CharField('title', max_length=255),
            description=models.CharField('description', max_length=255),
        )
        placeholder_1 = PlaceholderField('placeholder_1')

        def __unicode__(self):
            return self.title

Be sure to combine both hvad's :class:`TranslatableAdmin` and :class:`~cms.admin.placeholderadmin.PlaceholderAdmin` when
registering your model with the admin site::

    from cms.admin.placeholderadmin import PlaceholderAdmin
    from django.contrib import admin
    from hvad.admin import TranslatableAdmin
    from myapp.models import MultilingualExample1

    class MultilingualModelAdmin(TranslatableAdmin, PlaceholderAdmin):
        pass

    admin.site.register(MultilingualExample1, MultilingualModelAdmin)

Templates
=========

Now to render the placeholder in a template you use the
:ttag:`render_placeholder` tag from the
:mod:`~cms.templatetags.placeholder_tags` template tag library:

.. code-block:: html+django

    {% load placeholder_tags %}

    {% render_placeholder mymodel_instance.my_placeholder "640" %}

The :ttag:`render_placeholder` tag takes a
:class:`~cms.models.fields.PlaceholderField` instance as its first argument and
optionally accepts a width parameter as its second argument for context sensitive
plugins. The view in which you render your placeholder field must return the
:attr:`request <django.http.HttpRequest>` object in the context. This is
typically achieved in Django applications by using :class:`RequestContext`::

    from django.shortcuts import get_object_or_404, render_to_response
    from django.template.context import RequestContext
    from myapp.models import MyModel

    def my_model_detail(request, id):
        object = get_object_or_404(MyModel, id=id)
        return render_to_response('my_model_detail.html', {
            'object': object,
        }, context_instance=RequestContext(request))

If you want to render plugins from a specific language, you can use the tag
like this:

.. code-block:: html+django

    {% load placeholder_tags %}

    {% render_placeholder mymodel_instance.my_placeholder language 'en' %}

*******************************
Adding content to a placeholder
*******************************

There are two ways to add or edit content to a placeholder, the front-end admin
view and the back-end view.

Using the front-end editor
==========================

Probably the simplest way to add content to a placeholder, simply visit the
page displaying your model (where you put the :ttag:`render_placeholder` tag),
then append ``?edit`` to the page's URL. This will make a top banner appear,
and after switching the "Edit mode" button to "on", the banner will prompt you
for your username and password (the user should be allowed to edit the page,
obviously).

You are now using the so-called *front-end edit mode*:

|edit-banner|

.. |edit-banner| image:: ../images/edit-banner.png

Once in Front-end editing mode, your placeholders should display a menu,
allowing you to add plugins to them. The following screen shot shows a
default selection of plugins in an empty placeholder.

|frontend-placeholder-add-plugin|

.. |frontend-placeholder-add-plugin| image:: ../images/frontend-placeholder-add-plugin.png

Plugins are rendered at once, so you can get an idea how it will look
`in fine`. However, to view the final look of a plugin simply leave edit mode by
clicking the "Edit mode" button in the banner again.

.. _placeholder_object_permissions:

Permissions
===========

To be able to edit placeholder user has to be staff member and either has to
have edit permission on model that contains :class:`~cms.models.fields.PlaceholderField`
or has to have edit permission on that specific object of that model.

Model permissions are usually added through default django auth application
and its admin interface. On the other hand, object permission can be handled by
writing custom Auth Backend as described in 
`django docs <https://docs.djangoproject.com/en/1.5/topics/auth/customizing/#handling-object-permissions>`_
For example, if there is a ``UserProfile`` model that contains placeholder field
then custom backend can have following ``has_perm`` method that grants all rights
to current user only on his ``UserProfile`` object::

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_staff:
            return False
        if isinstance(obj, UserProfile):
            if user_obj.get_profile()==obj:
                return True
        return False


*********
Fieldsets
*********

There are some hard restrictions if you want to add custom fieldsets to an
admin page with at least one :class:`~cms.models.fields.PlaceholderField`:

1. Every :class:`~cms.models.fields.PlaceholderField` **must** be in its own
   :attr:`fieldset <django.contrib.admin.ModelAdmin.fieldsets>`, one
   :class:`~cms.models.fields.PlaceholderField` per fieldset.
2. You **must** include the following two classes: ``'plugin-holder'`` and
   ``'plugin-holder-nopage'``


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad

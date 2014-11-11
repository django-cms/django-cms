############################
Placeholders outside the CMS
############################

Placeholders are special model fields that django CMS uses to render
user-editable content (plugins) in templates. That is, it's the place where a
user can add text, video or any other plugin to a webpage, using the same
`frontend editing` as the CMS pages.

Placeholders can be viewed as containers for :class:`CMSPlugin` instances, and
can be used outside the CMS in custom applications using the
:class:`~cms.models.fields.PlaceholderField`.

By defining one (or several) :class:`~cms.models.fields.PlaceholderField` on a
custom model you can take advantage of the full power of :class:`CMSPlugin`.

.. warning::

    Screenshots are not in sync with the 3.0 UI at the moment, they will be
    updated once the new UI will be finalized; for the same reason, you'll find
    minor difference in the UI description.

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
    :class:`~cms.models.fields.PlaceholderField` may not be suppressed using
    ``'+'`` to allow the cms to check permissions properly. Attempting to do
    so will raise a :exc:`ValueError`.

.. note::

    If you add a PlaceholderField to an existing model, you'll be able to see
    the placeholder on the frontend editor only after saving each instance.


Admin Integration
=================

.. versionchanged:: 3.0

If you install this model in the admin application, you have to use the mixin
:class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` together with,
and must precede, :class:`~django.contrib.admin.ModelAdmin` so that the interface renders
correctly::

    from django.contrib import admin
    from cms.admin.placeholderadmin import PlaceholderAdminMixin
    from myapp.models import MyModel

    class MyModelAdmin(PlaceholderAdminMixin, admin.ModelAdmin):
        pass

    admin.site.register(MyModel, MyModelAdmin)

.. warning::

    Since 3.0 placeholder content can only be modified from the
    frontend, and thus placeholderfields **must** not be present in any
    ``fieldsets``, ``fields``, ``form`` or other modeladmin fields definition
    attribute.


I18N Placeholders
=================

Out of the box :class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` supports multiple
languages and will display language tabs. If you extend your model admin class derived from
`PlaceholderAdminMixin` and overwrite `change_form_template` be sure to have a look at
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

Be sure to combine both hvad's :class:`TranslatableAdmin` and :class:`~cms.admin.placeholderadmin.PlaceholderAdminMixin` when
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

Now to render the placeholder in a template you use the
:ttag:`render_placeholder` tag from the
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

    {% load cms_tags %}

    {% render_placeholder mymodel_instance.my_placeholder language 'en' %}

*******************************
Adding content to a placeholder
*******************************

.. versionchanged:: 3.0

Placeholders can be edited from the frontend by visiting the
page displaying your model (where you put the :ttag:`render_placeholder` tag),
then append ``?edit`` to the page's URL.
This will make the frontend editor top banner appear, and will eventually
require you to login.

If you need change ``?edit`` to custom string (eq: ``?admin_on``) you may
set ``CMS_TOOLBAR_URL__EDIT_ON`` variable in yours ``settings.py`` to
``"admin_on"``.

Also you may change ``?edit_off`` or ``?build`` to custom string with
set ``CMS_TOOLBAR_URL__EDIT_OFF`` or ``CMS_TOOLBAR_URL__BUILD`` variables
in yours ``settings.py``.

Notice: when you changing  ``CMS_TOOLBAR_URL__EDIT_ON`` or
``CMS_TOOLBAR_URL__EDIT_OFF`` or ``CMS_TOOLBAR_URL__BUILD`` please be
careful because you may replace reserved strings in system (eq:
``?page``). We recommended you use unique strings for this option
(eq: ``secret_admin`` or ``company_name``).

You are now using the so-called *frontend edit mode*:

|edit-banner|

.. |edit-banner| image:: ../images/edit-banner.png

Once in Front-end editing mode, switch to **Structure mode**, and you should be
able to see an outline of the placeholder, and a menu, allowing you to add
plugins to them. The following screenshot shows a default selection of plugins
in an empty placeholder.

|frontend-placeholder-add-plugin|

.. |frontend-placeholder-add-plugin| image:: ../images/frontend-placeholder-add-plugin.png

Adding the plugins automatically update the model content and they are rendered
in realtime.

There is no automatic draft / live version of general Django models, so plugins
content is updated instantly whenever you add / edit them.

.. _placeholder_object_permissions:

Permissions
===========

To be able to edit placeholder user has to be staff member and either has to
have edit permission on model that contains :class:`~cms.models.fields.PlaceholderField`
or has to have edit permission on that specific object of that model.

Model permissions are usually added through default django auth application
and its admin interface. On the other hand, object permission can be handled by
writing custom Auth Backend as described in 
`django docs <https://docs.djangoproject.com/en/1.7/topics/auth/customizing/#handling-object-permissions>`_
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


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad

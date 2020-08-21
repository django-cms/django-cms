.. _complex_apphooks_how_to:

###########################################
How to manage complex apphook configuration
###########################################

In :ref:`apphooks_how_to` we discuss some basic points of using apphooks. In this document we will cover some more
complex implementation possibilities.


.. _multi_apphook:

***************************************
Attaching an application multiple times
***************************************

Define a namespace at class-level
=================================

If you want to attach an application multiple times to different pages, then the class defining the apphook *must*
have an ``app_name`` attribute::

    class MyApphook(CMSApp):
        name = _("My Apphook")
        app_name = "myapp"

        def get_urls(self, page=None, language=None, **kwargs):
            return ["myapp.urls"]

The ``app_name`` does three key things:

* It provides the *fallback namespace* for views and templates that reverse URLs.
* It exposes the *Application instance name* field in the page admin when applying an apphook.
* It sets the *default apphook instance name* (which you'll see in the *Application instance name* field).

We'll explain these with an example. Let's suppose that your application's views or templates use
``reverse('myapp:index')`` or ``{% url 'myapp:index' %}``.

In this case the namespace of any apphooks you apply must match ``myapp``. If they don't, your pages using them will
throw up a ``NoReverseMatch`` error.

You can set the namespace for the instance of the apphook in the *Application instance name* field. However, you'll
need to set that to something *different* if an instance with that value already exists. In this case, as long as
``app_name = "myapp"`` it doesn't matter; even if the system doesn't find a match with the name of the instance it will
fall back to the one hard-wired into the class.

In other words setting ``app_name`` correctly guarantees that URL-reversing will work, because it sets the fallback
namespace appropriately.


Set a namespace at instance-level
=================================

On the other hand, the *Application instance name* will override the ``app_name`` *if* a match is found.

This arrangement allows you to use multiple application instances and namespaces if that flexibility is required, while
guaranteeing a simple way to make it work when it's not.

Django's :ref:`django:topics-http-reversing-url-namespaces` documentation provides more information on how this works,
but the simplified version is:

1. First, it'll try to find a match for the *Application instance name*.
2. If it fails, it will try to find a match for the ``app_name``.


.. _apphook_configurations:

**********************
Apphook configurations
**********************

Namespacing your apphooks also makes it possible to manage additional database-stored apphook configuration, on an
instance-by-instance basis.


Basic concepts
==============

To capture the configuration that different instances of an apphook can take, a Django model needs to be created - each
apphook instance will be an instance of that model, and administered through the Django admin in the usual way.

Once set up, an apphook configuration can be applied to to an apphook instance, in the *Advanced settings* of the page
the apphook instance belongs to:

.. image:: /how_to/images/select_apphook_configuration.png
   :alt: selecting an apphook configuration application
   :width: 400
   :align: center

The configuration is then loaded in the application's views for that namespace, and will be used to determined how it
behaves.

Creating an application configuration in fact creates an apphook instance namespace. Once created, the namespace of a
configuration cannot be changed - if a different namespace is required, a new configuration will also need to be
created.


********************************
An example apphook configuration
********************************

In order to illustrate how this all works, we'll create a new FAQ application, that provides a simple list
of questions and answers, together with an apphook class and an apphook configuration model that allows it to
exist in multiple places on the site in multiple configurations.

We'll assume that you have a working django CMS project running already.

Using helper applications
=========================

We'll use a couple of simple helper applications for this example, just to make our work easier.


Aldryn Apphooks Config
----------------------

`Aldryn Apphooks Config <https://github.com/aldryn/aldryn-apphooks-config>`_ is a helper application that makes it
easier to develop configurable apphooks. For example, it provides an ``AppHookConfig`` for you to subclass, and other
useful components to save you time.

In this example, we'll use Aldryn Apphooks Config, as we recommend it. However, you don't have to use it in your own
projects; if you prefer to can build the code you require by hand.

Use ``pip install aldryn-apphooks-config`` to install it.

Aldryn Apphooks Config in turn installs `Django AppData <https://github.com/ella/django-appdata>`_, which provides an
elegant way for an application to extend another; we'll make use of this too.


Create the new FAQ application
==============================

.. code-block:: shell

    python manage.py startapp faq


Create the FAQ ``Entry`` model
------------------------------

``models.py``:

.. code-block:: python

    from aldryn_apphooks_config.fields import AppHookConfigField
    from aldryn_apphooks_config.managers import AppHookConfigManager
    from django.db import models
    from faq.cms_appconfig import FaqConfig


    class Entry(models.Model):
        app_config = AppHookConfigField(FaqConfig)
        question = models.TextField(blank=True, default='')
        answer = models.TextField()

        objects = AppHookConfigManager()

        def __unicode__(self):
            return self.question

        class Meta:
            verbose_name_plural = 'entries'

The ``app_config`` field is a ``ForeignKey`` to an apphook configuration model; we'll create it in a moment. This model
will hold the specific namespace configuration, and makes it possible to assign each FAQ Entry to a namespace.

The custom ``AppHookConfigManager`` is there to make it easy to filter the queryset of ``Entries`` using a convenient
shortcut: ``Entry.objects.namespace('foobar')``.


Define the AppHookConfig subclass
---------------------------------

In a new file ``cms_appconfig.py`` in the FAQ application:

.. code-block:: python

    from aldryn_apphooks_config.models import AppHookConfig
    from aldryn_apphooks_config.utils import setup_config
    from app_data import AppDataForm
    from django.db import models
    from django import forms
    from django.utils.translation import gettext_lazy as _


    class FaqConfig(AppHookConfig):
        paginate_by = models.PositiveIntegerField(
            _('Paginate size'),
            blank=False,
            default=5,
        )


    class FaqConfigForm(AppDataForm):
        title = forms.CharField()
    setup_config(FaqConfigForm, FaqConfig)

The implementation *can* be left completely empty, as the minimal schema is already defined in
the abstract parent model provided by Aldryn Apphooks Config.

Here though we're defining an extra field on model, ``paginate_by``. We'll use it later
to control how many entries should be displayed per page.

We also set up a ``FaqConfigForm``, which uses ``AppDataForm`` to add a field to ``FaqConfig`` without actually
touching its model.

The title field could also just be a model field, like ``paginate_by``. But we're using the AppDataForm to demonstrate
this capability.


Define its admin properties
---------------------------

In ``admin.py`` we need to define all fields we'd like to display:

.. code-block:: python

    from django.contrib import admin
    from .cms_appconfig import FaqConfig
    from .models import Entry
    from aldryn_apphooks_config.admin import ModelAppHookConfig, BaseAppHookConfig


    class EntryAdmin(ModelAppHookConfig, admin.ModelAdmin):
        list_display = (
            'question',
            'answer',
            'app_config',
        )
        list_filter = (
            'app_config',
        )
    admin.site.register(Entry, EntryAdmin)


    class FaqConfigAdmin(BaseAppHookConfig, admin.ModelAdmin):
        def get_config_fields(self):
            return (
                'paginate_by',
                'config.title',
            )
    admin.site.register(FaqConfig, FaqConfigAdmin)

``get_config_fields`` defines the fields that should be displayed. Any fields
using the AppData forms need to be prefixed by ``config.``.


Define the apphook itself
-------------------------

Now let's create the apphook, and set it up with support for multiple instances. In ``cms_apps.py``:

.. code-block:: python

    from aldryn_apphooks_config.app_base import CMSConfigApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import gettext_lazy as _
    from .cms_appconfig import FaqConfig


    @apphook_pool.register
    class FaqApp(CMSConfigApp):
        name = _("Faq App")
        app_name = "faq"
        app_config = FaqConfig

        def get_urls(self, page=None, language=None, **kwargs):
            return ["faq.urls"]


Define a list view for FAQ entries
----------------------------------

We have all the basics in place. Now we'll add a list view for the FAQ entries
that only displays entries for the currently used namespace. In ``views.py``:

.. code-block:: python

    from aldryn_apphooks_config.mixins import AppConfigMixin
    from django.views import generic
    from .models import Entry


    class IndexView(AppConfigMixin, generic.ListView):
        model = Entry
        template_name = 'faq/index.html'

        def get_queryset(self):
            qs = super().get_queryset()
            return qs.namespace(self.namespace)

        def get_paginate_by(self, queryset):
            try:
                return self.config.paginate_by
            except AttributeError:
                return 10


``AppConfigMixin`` saves you the work of setting any attributes in your view - it automatically sets, for the view
class instance:

* current namespace in ``self.namespace``
* namespace configuration (the instance of FaqConfig) in ``self.config``
* current application in the ``current_app parameter`` passed to the
  ``Response`` class

In this case we're filtering to only show entries assigned to the current
namespace in ``get_queryset``. ``qs.namespace``, thanks to the model manager we defined earlier, is the equivalent of
``qs.filter(app_config__namespace=self.namespace)``.

In ``get_paginate_by`` we use the value from our appconfig model.


Define a template
^^^^^^^^^^^^^^^^^

In ``faq/templates/faq/index.html``:

.. code-block:: html+django

    {% extends 'base.html' %}

    {% block content %}
        <h1>{{ view.config.title }}</h1>
        <p>Namespace: {{ view.namespace }}</p>
        <dl>
            {% for entry in object_list %}
                <dt>{{ entry.question }}</dt>
                <dd>{{ entry.answer }}</dd>
            {% endfor %}
        </dl>

        {% if is_paginated %}
            <div class="pagination">
                <span class="step-links">
                    {% if page_obj.has_previous %}
                        <a href="?page={{ page_obj.previous_page_number }}">previous</a>
                    {% else %}
                        previous
                    {% endif %}

                    <span class="current">
                        Page {{ page_obj.number }} of {{ page_obj.paginator.num_pages }}.
                    </span>

                    {% if page_obj.has_next %}
                        <a href="?page={{ page_obj.next_page_number }}">next</a>
                    {% else %}
                        next
                    {% endif %}
                </span>
            </div>
        {% endif %}
    {% endblock %}


URLconf
^^^^^^^

``urls.py``:

.. code-block:: python

    from django.urls import re_path
    from . import views


    urlpatterns = [
        re_path(r'^$', views.IndexView.as_view(), name='index'),
    ]


Put it all together
===================

Finally, we add ``faq`` to ``INSTALLED_APPS``, then create and run migrations:

.. code-block:: shell

    python manage.py makemigrations faq
    python manage.py migrate faq

Now we should be all set.

Create two pages with the ``faq`` apphook (don't forget to publish them), with different namespaces and different
configurations. Also create some entries assigned to the two namespaces.

You can experiment with the different configured behaviours (in this case, only pagination is available), and the way
that different ``Entry`` instances can be associated with a specific apphook.

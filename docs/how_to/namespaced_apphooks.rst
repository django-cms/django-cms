###################
Namespaced Apphooks
###################


Namespaced configuration for apphooks allows to have multiple instances of the
same app be used in different locations in the page tree. This also provides
the building blocks needed to have some extra configuration in the database to
control some aspects of each instance of the app.

We'll illustrate this example with a new application.

Basic concepts
##############

The concept of apphook configuration is to store all the configuration in an
applications-specific model, and let the developer specify the desired options
in a form. In the views the configuration model instance specific for the
current application namespace is loaded (through a mixin) and thus it is
available in the view to provide the configuration for the current namespace.

Namespaces can be created on the fly in the Page admin Advanced settings.

When creating an application configuration, you are in fact defining a
namespace, which is saved in the same field in the Page model as the
plain namespaces.


step-by-step implementation
###########################

We're going to create a new application called FAQ. It is a simple list
of Frequently asked questions. And we'll make it possible to setup multiple
sets of FAQ Entries at different locations of the page tree, each with its
individual set of entries.

Lets create our new FAQ app:

.. code-block:: shell

    python manage.py startapp faq

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

The ``app_config`` field is essentially a ``ForeignKey`` to a model we'll
define in the next step. That model will hold the specific namespace
configuration and allows to assign an Entry to a namespace.

The custom ``AppHookConfigManager`` simply makes the default queryset
easily filterable by the namespace like this:
``Entry.objects.namespace('foobar')``.

Next lets define the AppHookConfig model (in ``cms_appconfig.py``):

.. code-block:: python

    from aldryn_apphooks_config.models import AppHookConfig
    from aldryn_apphooks_config.utils import setup_config
    from app_data import AppDataForm
    from django.db import models
    from django import forms
    from django.utils.translation import ugettext_lazy as _


    class FaqConfig(AppHookConfig):
        paginate_by = models.PositiveIntegerField(
            _('Paginate size'),
            blank=False,
            default=5,
        )


    class FaqConfigForm(AppDataForm):
        title = forms.CharField()
    setup_config(FaqConfigForm, FaqConfig)

The implementation can be completely empty as the minimal schema is defined in
the parent (abstract) model.

In this case we're defining a few extra fields though. We're defining
``paginate_by`` as a normal model field. We'll use it later to control how
many entries should be displayed per page. For the title, we're using a
``AppDataForm`` (see django-appdata). These forms can also be extended from
other applications by just registering them. So other apps can add
fields without altering the model (it's saved in a json field).
The title field could also just be a model field, like ``paginate_by``. But
we're using the AppDataForm to demonstrate this capability.

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

Now lets create the apphook with appconfig support (``cms_apps.py``):

.. code-block:: python

    from aldryn_apphooks_config.app_base import CMSConfigApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _
    from .cms_appconfig import FaqConfig


    class FaqApp(CMSConfigApp):
        name = _("Faq App")
        urls = ["faq.urls"]
        app_name = "faq"
        app_config = FaqConfig

    apphook_pool.register(FaqApp)


We have all the basics in place. Now we'll add a list view for the FAQ entries
that only displays entries for the currently used namespace (``views.py``):

.. code-block:: python

    from aldryn_apphooks_config.mixins import AppConfigMixin
    from django.views import generic
    from .models import Entry


    class IndexView(AppConfigMixin, generic.ListView):
        model = Entry
        template_name = 'faq/index.html'

        def get_queryset(self):
            qs = super(IndexView, self).get_queryset()
            return qs.namespace(self.namespace)

        def get_paginate_by(self, queryset):
            try:
                return self.config.paginate_by
            except AttributeError:
                return 10

AppConfigMixin provides a complete support to namespaces, so the view is not
required to set anything specific to support them; the following attributes are
set for the view class instance:

* current namespace in ``self.namespace``
* namespace configuration (the instance of FaqConfig) in ``self.config``
* current application in the ``current_app parameter`` passed to the
  ``Response`` class

In this case we're filtering to only show entries assigned to the current
namespace in ``get_queryset``. There is no magic behind ``qs.namespace``, it
could have also been written as
``qs.filter(app_config__namespace=self.namespace)``.

In ``get_paginate_by`` we use the value from our appconfig model.

And now for the rest of the missing files of the FAQ app.

And the template (``faq/templates/faq/index.html``):

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

``urls.py``:

.. code-block:: python

    from django.conf.urls import url
    from . import views


    urlpatterns = [
        url(r'^$', views.IndexView.as_view(), name='index'),
    ]

Finally, lets add ``faq`` to ``INSTALLED_APPS`` and create a migrations:

.. code-block:: shell

    python manage.py makemigrations faq
    python manage.py migrate faq

Now we should be all set. Create two pages with the ``faq`` apphook with different
namespaces and different configurations. Also create some entries assigned to
the two namespaces. Don't forget to publish the pages with the apphook and
restart the server.

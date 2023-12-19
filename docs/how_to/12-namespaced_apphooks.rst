.. _complex_apphooks_how_to:

How to manage complex apphook configuration
===========================================

In :ref:`apphooks_how_to` we discuss some basic points of using apphooks. In this
document we will cover some more complex implementation possibilities.

.. _multi_apphook:

Attaching an application multiple times
---------------------------------------

Define a namespace at class-level
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to attach an application multiple times to different pages, then the class
defining the apphook *must* have an ``app_name`` attribute:

.. code-block::

    class MyApphook(CMSApp):
        name = _("My Apphook")
        app_name = "myapp"

        def get_urls(self, page=None, language=None, **kwargs):
            return ["myapp.urls"]

The ``app_name`` does three key things:

- It provides the *fallback namespace* for views and templates that reverse URLs.
- It exposes the *Application instance name* field in the page admin when applying an
  apphook.
- It sets the *default apphook instance name* (which you'll see in the *Application
  instance name* field).

We'll explain these with an example. Let's suppose that your application's views or
templates use ``reverse('myapp:index')`` or ``{% url 'myapp:index' %}``.

In this case the namespace of any apphooks you apply must match ``myapp``. If they
don't, your pages using them will throw up a ``NoReverseMatch`` error.

You can set the namespace for the instance of the apphook in the *Application instance
name* field. However, you'll need to set that to something *different* if an instance
with that value already exists. In this case, as long as ``app_name = "myapp"`` it
doesn't matter; even if the system doesn't find a match with the name of the instance it
will fall back to the one hard-wired into the class.

In other words setting ``app_name`` correctly guarantees that URL-reversing will work,
because it sets the fallback namespace appropriately.

Set a namespace at instance-level
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the other hand, the *Application instance name* will override the ``app_name`` *if* a
match is found.

This arrangement allows you to use multiple application instances and namespaces if that
flexibility is required, while guaranteeing a simple way to make it work when it's not.

Django's :ref:`django:topics-http-reversing-url-namespaces` documentation provides more
information on how this works, but the simplified version is:

1. First, it will try to find a match for the *Application instance name*.
2. If it fails, it will try to find a match for the ``app_name``.

.. _apphook_configurations:

Apphook configurations
----------------------

Namespacing your apphooks also makes it possible to manage additional database-stored
apphook configuration, on an instance-by-instance basis.

Basic concepts
~~~~~~~~~~~~~~

To capture the configuration that different instances of an apphook can take, a Django
model needs to be created - each apphook instance will be an instance of that model, and
administered through the Django admin in the usual way.

Once set up, an apphook configuration can be applied to to an apphook instance, in the
*Advanced settings* of the page the apphook instance belongs to:

.. image:: /how_to/images/select_apphook_configuration.png
    :alt: selecting an apphook configuration application
    :width: 400
    :align: center

The configuration is then loaded in the application's views for that namespace, and will
be used to determined how it behaves.

Creating an application configuration in fact creates an apphook instance namespace.
Once created, the namespace of a configuration cannot be changed - if a different
namespace is required, a new configuration will also need to be created.

An example apphook configuration
--------------------------------

In order to illustrate how this all works, we’ll create a new FAQ application, that
provides a simple list of questions and answers, together with an apphook class and an
apphook configuration model that allows it to exist in multiple places on the site in
multiple configurations.

We’ll assume that you have a working django CMS project running already.

Create the new FAQ application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let us quickly create the new app:

1. **Create a new app in your project**:

   .. code-block::

       python -m manage startapp faq

2. **Create a model for the app config in ``models.py``**: The app config will be
   identified by its namespace.

   .. code-block::

       from django.db import models
       from django.utils.translation import gettext_lazy as _


       class FaqConfigModel(models.Model):
           namespace = models.CharField(
               _("instance namespace"),
               default=None,
               max_length=100,
               unique=True,
           )

           paginate_by = models.PositiveIntegerField(
               _("paginate size"),
               blank=False,
               default=5,
           )

3. **Create the FAQ model** also in ``models.py``: All entries will be assigned to an
   instance of the app hook.

   .. code-block::

       class Entry(models.Model):
           app_config = models.ForeignKey(FaqConfigModel, null=False)  # We need to assign an FAQ entry to its app instance
           question = models.TextField(blank=True, default='')
           answer = models.TextField()

           def __str__(self):
               return self.question or "<Empty question>"

           class Meta:
               verbose_name_plural = 'entries'

4. **Create the FAQ CMS app**: In the apps's ``cms_apps.py`` create the ``FaqConfig``
   class. This extensions tells django CMS how to get the app config instances.

   .. code-block::

       from django.core.exceptions import ObjectDoesNotExist
       from django.urls import reverse

       from cms.app_base import CMSApp
       from cms.apphook_pool import apphook_pool

       from .models import FaqConfigModel


       @apphook_pool.register
       class FaqConfig(CMSApp):
           name = "FAQ"
           app_config = FaqConfigModel

           def get_urls(self, page=None, language=None, **kwargs):
               return ["faq.urls"]

           def get_configs(self):
               return self.app_config.objects.all()

           def get_config(self, namespace):
               try:
                   return self.app_config.objects.get(namespace=namespace)
               except ObjectDoesNotExist:
                   return None

          def  get_config_add_url(self):
               try:
                  return reverse("admin:{}_{}_add".format(self.app_config._meta.app_label, self.app_config._meta.model_name))
               except AttributeError:
                   return reverse(
                       "admin:{}_{}_add".format(self.app_config._meta.app_label, self.app_config._meta.module_name)
                   )

5. **Add models to the admin interface**: Its admin properties are defined in
   ``admin.py``:

   .. code-block::

       from django.contrib import admin

       from . import models


       @admin.register(models.Entry)
       class EntryAdmin(admin.ModelAdmin):
           list_display = (
               'question',
               'answer',
               'app_config',
           )
           list_filter = (
               'app_config',
           )


       @admin.register(models.FaqConfigModel)
       class FaqConfigAdmin(admin.ModelAdmin):
           pass

6. **Create a simple list view** in ``views.py``: For the views there is a catch: The
   view will have to determine which app instance it is showing. Here's a short reusable
   mixin to help with that:

   .. code-block::

       from django.views.generic import ListView
       from django.urls import Resolver404, resolve
       from django.utils.translation import override

       from cms.apphook_pool import apphook_pool
       from cms.utils import get_language_from_request

       from . import models


       def get_app_instance(request):
           namespace, config = "", None
           if getattr(request, "current_page", None) and request.current_page.application_urls:
               app = apphook_pool.get_apphook(request.current_page.application_urls)
               if app and app.app_config:
                   try:
                       config = None
                       with override(get_language_from_request(request)):
                           if hasattr(request, "toolbar") and hasattr(request.toolbar, "request_path"):
                               path = request.toolbar.request_path  # If v4 endpoint take request_path from toolbar
                           else:
                               path = request.path_info
                           namespace = resolve(path).namespace
                           config = app.get_config(namespace)
                   except Resolver404:
                       pass
           return namespace, config


       class AppHookConfigMixin:
           def dispatch(self, request, *args, **kwargs):
               # get namespace and config
               self.namespace, self.config = get_app_instance(request)
               request.current_app = self.namespace
               return super().dispatch(request, *args, **kwargs)

           def get_queryset(self):
               qs = super().get_queryset()
               return qs.filter(app_config__namespace=self.namespace)


       class IndexView(AppHookConfigMixin, ListView):
           model = models.Entry
           template_name = 'faq/index.html'

           def get_paginate_by(self, queryset):
               try:
                   return self.config.paginate_by
               except AttributeError:
                   return 10

7. **Declare the app's URLs** in ``urls.py``: .. code-block:

   .. code-block::

       from django.urls import path
       from . import views


       urlpatterns = [
           path("", views.IndexView.as_view(), name='index'),
       ]

8. Finally, **create a template for the index view**: .. code-block:

   .. code-block::

       {% extends 'base.html' %}

       {% block content %}
           <h1>Namespace: {{ view.namespace }}</h1>
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

Put it all together
~~~~~~~~~~~~~~~~~~~

Finally, we add ``"faq"`` to ``INSTALLED_APPS``, then create and run migrations:

.. code-block::

    python -m manage makemigrations faq
    python -m manage migrate faq

Now we should be all set.

Create two pages with the faq apphook, with different namespaces and different
configurations. Also create some entries assigned to the two namespaces.

You can experiment with the different configured behaviours (in this case, only
pagination is available), and the way that different Entry instances can be associated
with a specific apphook.

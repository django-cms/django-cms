.. _apphooks_how_to:

######################
How to create apphooks
######################

An **apphook** allows you to attach a Django application to a page. For example,
you might have a news application that you'd like integrated with django CMS. In
this case, you can create a normal django CMS page without any content of its
own, and attach the news application to the page; the news application's content
will be delivered at the page's URL.

All URLs in that URL path will be passed to the attached application's URL configs.

The :ref:`Tutorials <tutorials>` section contains a basic guide to :ref:`getting started with apphooks
<apphooks_introduction>`. This document assumes more familiarity with the CMS generally.


******************************
The basics of apphook creation
******************************

To create an apphook, create a ``cms_apps.py`` file in your application.

.. note:: Up to version 3.1 this module was named ``cms_app.py`` - please
          update your existing modules to the new naming convention.
          Support for the old name will be removed in version 3.4.

The file needs to contain a :class:`CMSApp <cms.app_base.CMSApp>` sub-class. For example::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _

    class MyApphook(CMSApp):
        name = _("My Apphook")

        def get_urls(self, page=None, language=None, **kwargs):
            return ["myapp.urls"]       # replace this with the path to your application's URLs module

    apphook_pool.register(MyApphook)

.. versionchanged:: 3.3
    ``CMSApp.get_urls()`` replaces ``CMSApp.urls``. ``urls`` is now deprecated and will be removed in
    version 3.5.


Apphooks for namespaced applications
====================================

Does your application use :ref:`namespaced URLs <django:topics-http-defining-url-namespaces>`? This is good practice,
so it should!

In that case you will need to ensure that your apphooks include its URLs in the right namespace. Add an ``app_name``
attribute to the class that reflects the way you'd include the applications' URLs into your project.

For example, if your application requires that your project's URLs do::

    url(r'^myapp/', include('myapp.urls', app_name='myapp')),

then your ``MyApphook`` class should include::

    app_name = "myapp"

If you fail to this, then any templates in the application that invoke URLs using the form ``{% url 'myapp:index' %}``
or views that call (for example) ``reverse('myapp:index')`` will throw a ``NoReverseMatch`` error.

*Unless* the class that defines the apphook specifies an ``app_name``, it can be attached only to one page at a time.
Attempting to apply it a second times will cause an error. See :ref:`multi_apphook` for more on having multiple apphook
instances.


.. _reloading_apphooks:

Loading new and re-configured apphooks
======================================

Certain apphook-related changes require server restarts in order to be loaded.

Whenever you:

* add or remove an apphook
* change the slug of a page containing an apphook or the slug of a page which has a descendant with an apphook

the URL caches must be reloaded.

If you have the :ref:`ApphookReloadMiddleware` installed, which is recommended, the server will do it for your by
re-initialising the URL patterns automatically.

Otherwise, you will need to restart it manually.


****************
Using an apphook
****************

Once your apphook has been set up and loaded, you'll now be able to select the *Application* that's hooked into that page from its *Advanced settings*.

.. note::

    An apphook won't actually do anything until the page it belongs to is published. Take note that this also
    means all parent pages must also be published.

The apphook attaches all of the apphooked application's URLs to the page; its root URL will be the page's own URL, and
any lower-level URLs will be on the same URL path.

So, given an application with the ``urls.py``::

    from django.conf.urls import *

    urlpatterns = patterns('sampleapp.views',
        url(r'^$', 'main_view', name='app_main'),
        url(r'^sublevel/$', 'sample_view', name='app_sublevel'),
    )

attached to a page whose URL path is ``/hello/world/``, its views will be exposed as follows:

* ``main_view`` at ``/hello/world/``
* ``sample_view`` at ``/hello/world/sublevel/``


Sub-pages of an apphooked page
==============================

Usually, it's simplest to leave an apphook to swallow up all the URLs below its page's URL.

However, as long as the application's urlconf is not too greedy and doesn't conflict with the URLs of any sub-pages,
those sub-pages can be reached. That is, although the apphooked application will have priority, any URLs it *doesn't*
consume will be available for ordinary django CMS pages, if they exist.


******************
Apphook management
******************

Uninstalling an apphook with applied instances
==============================================

If you remove an apphook class (in effect uninstalling it) from your system that still has instances applied to pages,
django CMS tries to handle this as gracefully as possible:

* Affected Pages still maintain a record of the applied apphook; if the apphook class is reinstated, it will work as
  before.
* The page list will show apphook indicators where appropriate.
* The page will otherwise behave like a normal django CMS page, and display its placeholders in the usual way.
* If you save the page's Advanced settings, the apphook will be removed.


Management commands
===================

You can clear uninstalled apphook instances using a CMS management command ``uninstall apphooks``; for example::

    manage.py cms uninstall apphooks MyApphook MyOtherApphook

You can get a list of installed apphooks using the :ref:`cms-list-command`; in this case::

    manage.py cms list apphooks

See the :ref:`Management commands reference <management_commands>` for more information.

.. _apphook_menus:

*************
Apphook menus
*************

Generally, it is recommended to allow the user to control whether a menu is attached to a page. However, an apphook can
be made to do this automatically if required. It will behave just as if it were attached the page using its *Advanced
settings*).

Menus can be added to an apphook using the ``get_menus()`` method. On the basis of the example above::

    # [...]
    from myapp.menu import MyAppMenu

    class MyApphook(CMSApp):
        # [...]
        def get_menus(self, page=None, language=None, **kwargs):
            return [MyAppMenu]

.. versionchanged:: 3.3
    ``CMSApp.get_menus()`` replaces ``CMSApp.menus``. The ``menus`` attribute is now deprecated and will be
    removed in version 3.5.


The menus returned in the ``get_menus()`` method need to return a list of nodes, in their ``get_nodes()`` methods. See
:ref:`integration_attach_menus` for more on creating menu classes that generate nodes.

You can return multiple menu classes; all will be attached to the same page::

    def get_menus(self, page=None, language=None, **kwargs):
        return [MyAppMenu, CategoryMenu]


.. _apphook_permissions:

*******************
Apphook permissions
*******************

By default the content represented by an apphook has the same permissions set as the page it is assigned to. So if for
example a page requires the user to be logged in, then the attached apphook and all its URLs will have the same
requirements.

To disable this behaviour set ``permissions = False`` on your apphook::

    class SampleApp(CMSApp):
        name = _("Sample App")
        _urls = ["project.sampleapp.urls"]
        permissions = False

If you still want some of your views to use the CMS's permission checks you can enable them via a decorator, ``cms.utils.decorators.cms_perms``

Here is a simple example::

    from cms.utils.decorators import cms_perms

    @cms_perms
    def my_view(request, **kw):
        ...

If you have your own permission checks in your application, then use ``exclude_permissions`` property of the apphook::

    class SampleApp(CMSApp):
        name = _("Sample App")
        permissions = True
        exclude_permissions = ["some_nested_app"]

        def get_urls(self, page=None, language=None, **kwargs):
            return ["project.sampleapp.urls"]

For example, django-oscar_ apphook integration needs to be used with ``exclude_permissions`` of the
dashboard app, because it uses the `customisable access function`__. So, your apphook in this case
will look like this::

    class OscarApp(CMSApp):
        name = _("Oscar")
        exclude_permissions = ['dashboard']

        def get_urls(self, page=None, language=None, **kwargs):
            return application.urls[0]

.. _django-oscar: https://github.com/tangentlabs/django-oscar
.. __: https://github.com/tangentlabs/django-oscar/blob/0.7.2/oscar/apps/dashboard/nav.py#L57


***********************************************
Automatically restart server on apphook changes
***********************************************

As mentioned above, whenever you:

* add or remove an apphook
* change the slug of a page containing an apphook
* change the slug of a page with a descendant with an apphook

The CMS the server will reload its URL caches. It does this by listening for
the signal ``cms.signals.urls_need_reloading``.

.. warning::

    This signal does not actually do anything itself. For automated server
    restarting you need to implement logic in your project that gets executed
    whenever this signal is fired. Because there are many ways of deploying
    Django applications, there is no way we can provide a generic solution for
    this problem that will always work.

.. warning::

    The signal is fired **after** a request. If you change something via an API
    you'll need a request for the signal to fire.


**************************************
Apphooks and placeholder template tags
**************************************

It's important to understand that while an apphooked application takes over the CMS page at that
location completely, depending on how the application's templates extend other templates, a
django CMS ``{% placeholder %}`` template tag may be invoked - **but will not work**.

``{% static_placeholder %}`` tags on the other hand are *not* page-specific and *will* function
normally.

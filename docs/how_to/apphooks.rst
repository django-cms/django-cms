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

The :ref:`Tutorials <tutorials>` section contains a basic guide to :ref:`getting started with
apphooks <apphooks_introduction>`. This document assumes more familiarity with the CMS generally.


******************************
The basics of apphook creation
******************************

To create an apphook, create a ``cms_apps.py`` file in your application.

The file needs to contain a :class:`CMSApp <cms.app_base.CMSApp>` sub-class. For example::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool

    @apphook_pool.register
    class MyApphook(CMSApp):
        app_name = "myapp"  # must match the application namespace
        name = "My Apphook"

        def get_urls(self, page=None, language=None, **kwargs):
            return ["myapp.urls"] # replace this with the path to your application's URLs module

.. versionchanged:: 3.3
    ``CMSApp.get_urls()`` replaces ``CMSApp.urls``. ``urls`` was removed
    in version 3.5.


Apphooks for namespaced applications
====================================

Your application should use :ref:`namespaced URLs <django:topics-http-defining-url-namespaces>`.

In the example above, the application uses the ``myapp`` namespace. Your ``CMSApp``
sub-class **must reflect the application's namespace** in the ``app_name`` attribute.

The application may specify a namespace by supplying an ``app_name`` in its ``urls.py``, or its
documentation might advise that you when include its URLs, you do it thus:

..  code-block:: python

    re_path(r'^myapp/', include('myapp.urls', app_name='myapp'))

If you fail to do this, then any templates in the application that invoke URLs using the form ``{% url
'myapp:index' %}`` or views that call (for example) ``reverse('myapp:index')`` will throw a
``NoReverseMatch`` error.


Apphooks for non-namespaced applications
----------------------------------------

If you are writing apphooks for third-party applications, you may find one that in fact does
not have an application namespace for its URLs. Such an application is liable to tun into namespace
conflicts, and doesn't represent good practice.

However if you *do* encounter such an application, your own apphook for it will need in turn to forgo the
``app_name`` attribute.

Note that unlike apphooks without ``app_name`` attributes can be attached only to one page at a
time; attempting to apply them a second time will cause an error. Only one instance of these
apphooks can exist.

See :ref:`multi_apphook` for more on having multiple apphook instances.


Returning apphook URLs manually
===============================

Instead of defining the URL patterns in another file ``myapp/urls.py``, it also is possible
to return them manually, for example if you need to override the set provided. An example:

..  code-block:: python

    from django.urls import re_path
    from myapp.views import SomeListView, SomeDetailView

    class MyApphook(CMSApp):
        # ...
        def get_urls(self, page=None, language=None, **kwargs):
            return [
                re_path(r'^$', SomeListView.as_view()),
                re_path(r'^(?P<slug>[\w-]+)/?$', SomeDetailView.as_view()),
            ]

However, it's much neater to keep them in the application's ``urls.py``, where they can easily be
reused.


.. _reloading_apphooks:

Loading new and re-configured apphooks
======================================

Certain apphook-related changes require server restarts in order to be loaded.

Whenever you:

* add or remove an apphook
* change the slug of a page containing an apphook or the slug of a page which has a descendant with
  an apphook

the URL caches must be reloaded.

If you have the :ref:`ApphookReloadMiddleware` installed, which is recommended, the server will do
it for you by re-initialising the URL patterns automatically.

Otherwise, you will need to restart the server manually.


****************
Using an apphook
****************

Once your apphook has been set up and loaded, you'll now be able to select the *Application* that's
hooked into that page from its *Advanced settings*.

.. note::

    An apphook won't actually do anything until the page it belongs to is published. Take note that
    this also means all parent pages must also be published.

The apphook attaches all of the apphooked application's URLs to the page; its root URL will be the
page's own URL, and any lower-level URLs will be on the same URL path.

So, given an application with the ``urls.py`` for the views ``index_view`` and ``archive_view``::

    urlpatterns = [
        re_path(r'^$', index_view),
        re_path(r'^archive/$', archive_view),
    ]

attached to a page whose URL path is ``/hello/world/``, the views will be exposed as follows:

* ``index_view`` at ``/hello/world/``
* ``archive_view`` at ``/hello/world/archive/``


Sub-pages of an apphooked page
==============================

..  important::

    Don't add child pages to a page with an apphook.

    The apphook "swallows" all URLs below that of the page, handing them over to the attached
    application. If you have any child pages of the apphooked page, django CMS will not be
    able to serve them reliably.


*****************
Managing apphooks
*****************

Uninstalling an apphook with applied instances
==============================================

If you remove an apphook class from your system (in effect uninstalling it) that still has
instances applied to pages, django CMS tries to handle this as gracefully as possible:

* Affected pages still maintain a record of the applied apphook; if the apphook class is
  subsequently reinstated, it will work as before.
* The page list will show apphook indicators where appropriate.
* The page will otherwise behave like a normal django CMS page, and display its placeholders in the
  usual way.
* If you save the page's *Advanced settings*, the apphook will be removed.


Management commands
===================

You can clear uninstalled apphook instances using the CMS management command ``uninstall apphooks``. For example::

    manage.py cms uninstall apphooks MyApphook MyOtherApphook

You can get a list of installed apphooks using the :ref:`cms-list-command`; in this case::

    manage.py cms list apphooks

See the :ref:`Management commands reference <management_commands>` for more information.


.. _apphook_menus:

************************
Adding menus to apphooks
************************

Generally, it is recommended to allow the user to control whether a menu is attached to a page (See
:ref:`integration_attach_menus` for more on these menus). However, an apphook can be made to do
this automatically if required. It will behave just as if the menu had been attached to the page
using its *Advanced settings*).

Menus can be added to an apphook using the ``get_menus()`` method. On the basis of the example above::

    # [...]
    from myapp.cms_menus import MyAppMenu

    class MyApphook(CMSApp):
        # [...]
        def get_menus(self, page=None, language=None, **kwargs):
            return [MyAppMenu]

.. versionchanged:: 3.3
    ``CMSApp.get_menus()`` replaces ``CMSApp.menus``. The ``menus`` attribute is now deprecated and
    has been removed in version 3.5.


The menus returned in the ``get_menus()`` method need to return a list of nodes, in their
``get_nodes()`` methods. :ref:`integration_attach_menus` has more information on creating menu
classes that generate nodes.

You can return multiple menu classes; all will be attached to the same page::

    def get_menus(self, page=None, language=None, **kwargs):
        return [MyAppMenu, CategoryMenu]


.. _apphook_permissions:

********************************
Managing permissions on apphooks
********************************

By default the content represented by an apphook has the same permissions set as the page it is
assigned to. So if for example a page requires the user to be logged in, then the attached apphook
and all its URLs will have the same requirements.

To disable this behaviour set ``permissions = False`` on your apphook::

    class MyApphook(CMSApp):
        [...]
        permissions = False

If you still want some of your views to use the CMS's permission checks you can enable them via a decorator, ``cms.utils.decorators.cms_perms``

Here is a simple example::

    from cms.utils.decorators import cms_perms

    @cms_perms
    def my_view(request, **kw):
        ...

If you make your own permission checks in your application, then use the ``exclude_permissions`` property of the apphook::

    class MyApphook(CMSApp):
        [...]
        permissions = True
        exclude_permissions = ["some_nested_app"]

where you provide the name of the application in question


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

    The signal is fired **after** a request - for example, upon saving a page's settings. If you
    change and apphook's setting via an API the signal won't fire until a subsequent request.


**************************************
Apphooks and placeholder template tags
**************************************

It's important to understand that while an apphooked application takes over the CMS page at that
location completely, depending on how the application's templates extend other templates, a
django CMS ``{% placeholder %}`` template tag may be invoked - **but will not work**.

``{% static_placeholder %}`` tags on the other hand are *not* page-specific and *will* function
normally.

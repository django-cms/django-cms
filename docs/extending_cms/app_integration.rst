###############
App Integration
###############

It is pretty easy to integrate your own Django applications with django CMS.
You have 5 ways of integrating your app:

1. Menus

    Static extend the menu entries

2. AttachMenus

    Attach your menu to a page.

3. App-Hooks

    Attach whole apps with optional menu to a page.

4. Navigation Modifiers

    Modify the whole menu tree

5. Custom Plugins

    Display your models / content in cms pages

*****
Menus
*****

Create a menu.py in your application and write the following inside::

    from menus.base import Menu, NavigationNode
    from menus.menu_pool import menu_pool
    from django.utils.translation import ugettext_lazy as _

    class TestMenu(Menu):

        def get_nodes(self, request):
            nodes = []
            n = NavigationNode(_('sample root page'), "/", 1)
            n2 = NavigationNode(_('sample settings page'), "/bye/", 2)
            n3 = NavigationNode(_('sample account page'), "/hello/", 3)
            n4 = NavigationNode(_('sample my profile page'), "/hello/world/", 4, 3)
            nodes.append(n)
            nodes.append(n2)
            nodes.append(n3)
            nodes.append(n4)
            return nodes

    menu_pool.register_menu(TestMenu)

If you refresh a page you should now see the menu entries from above.
The get_nodes function should return a list of
:class:`NavigationNode <menus.base.NavigationNode>` instances. A
:class:`NavigationNode` takes the following arguments:

- title

  What should the menu entry read?

- url,

  Link if menu entry is clicked.

- id

  A unique id for this menu.

- parent_id=None

  If this is a child of another node give here the id of the parent.

- parent_namespace=None

  If the parent node is not from this menu you can give it the parent
  namespace. The namespace is the name of the class. In the above example that
  would be: "TestMenu"

- attr=None

  A dictionary of additional attributes you may want to use in a modifier or
  in the template.

- visible=True

  Whether or not this menu item should be visible.

Additionally, each :class:`NavigationNode` provides a number of methods, which are
detailed in the :class:`NavigationNode <menus.base.NavigationNode>` API references.

************
Attach Menus
************

Classes that extend from :class:`menus.base.Menu` always get attached to the
root. But if you want the menu be attached to a CMS Page you can do that as
well.

Instead of extending from :class:`~menus.base.Menu` you need to extend from
:class:`cms.menu_bases.CMSAttachMenu` and you need to define a name. We will do
that with the example from above::


    from menus.base import NavigationNode
    from menus.menu_pool import menu_pool
    from django.utils.translation import ugettext_lazy as _
    from cms.menu_bases import CMSAttachMenu

    class TestMenu(CMSAttachMenu):

        name = _("test menu")

        def get_nodes(self, request):
            nodes = []
            n = NavigationNode(_('sample root page'), "/", 1)
            n2 = NavigationNode(_('sample settings page'), "/bye/", 2)
            n3 = NavigationNode(_('sample account page'), "/hello/", 3)
            n4 = NavigationNode(_('sample my profile page'), "/hello/world/", 4, 3)
            nodes.append(n)
            nodes.append(n2)
            nodes.append(n3)
            nodes.append(n4)
            return nodes

    menu_pool.register_menu(TestMenu)


Now you can link this Menu to a page in the 'Advanced' tab of the page
settings under attached menu.

Each must have a :meth:`get_menu_title` method, a
:meth:`~django.db.models.Model.get_absolute_url` method, and a ``childrens``
list with all of its children inside (the 's' at the end of ``childrens`` is
done on purpose because ``children`` is already taken by django-mptt).

Be sure that :meth:`get_menu_title` and :meth:`get_absolute_url` don't trigger
any queries when called in a template or you may have some serious performance
and database problems with a lot of queries.

It may be wise to cache the output of :meth:`~menu.base.Menu.get_nodes`. For
this you may need to write a wrapper class because of dynamic content that the
pickle module can't handle.

If you want to display some static pages in the navigation ("login", for
example) you can write your own "dummy" class that adheres to the conventions
described above.

A base class for this purpose can be found in ``cms/utils/navigation.py``


*********
App-Hooks
*********

With App-Hooks you can attach whole Django applications to pages. For example
you have a news app and you want it attached to your news page.

To create an apphook create a ``cms_app.py`` in your application. And in there
write the following::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _

    class MyApphook(CMSApp):
        name = _("My Apphook")
        urls = ["myapp.urls"]

    apphook_pool.register(MyApphook)

Replace ``myapp.urls`` with the path to your applications ``urls.py``.

Now edit a page and open the advanced settings tab. Select your new apphook
under "Application". Save the page.

.. warning::

    If you are on a multi-threaded server (mostly all webservers,
    except the dev-server): Restart the server because the URLs are cached by
    Django and in a multi-threaded environment we don't know which caches are
    cleared yet.
    
.. note::

    If at some point you want to remove this apphook after deleting the cms_app.py
    there is a cms management command called uninstall apphooks
    that removes the specified apphook(s) from all pages by name.
    eg. ``manage.py cms uninstall apphooks MyApphook``.
    To find all names for uninstallable apphooks there is a command for this aswell
    ``manage.py cms list apphooks``.

If you attached the app to a page with the url ``/hello/world/`` and the app has
a urls.py that looks like this::

    from django.conf.urls.defaults import *

    urlpatterns = patterns('sampleapp.views',
        url(r'^$', 'main_view', name='app_main'),
        url(r'^sublevel/$', 'sample_view', name='app_sublevel'),
    )

The ``main_view`` should now be available at ``/hello/world/`` and the
``sample_view`` has the url ``/hello/world/sublevel/``.


.. note::

    All views that are attached like this must return a
    :class:`~django.template.RequestContext` instance instead of the
    default :class:`~django.template.Context` instance.


Language Namespaces
-------------------

An additional feature of apphooks is that if you use the
:class:`cms.middleware.multilingual.MultilingualURLMiddleware` all apphook urls
are language namespaced.

What this means:

To reverse the first url from above you would use something like this in your
template:

.. code-block:: html+django

    {% url app_main %}

If you want to access the same url but in a different language use a langauge
namespace:

.. code-block:: html+django

    {% url de:app_main %}
    {% url en:app_main %}
    {% url fr:app_main %}

If you want to add a menu to that page as well that may represent some views
in your app add it to your apphook like this::

    from myapp.menu import MyAppMenu

    class MyApphook(CMSApp):
        name = _("My Apphook")
        urls = ["myapp.urls"]
        menus = [MyAppMenu]

    apphook_pool.register(MyApphook)


For an example if your app has a :class:`Category` model and you want this
category model to be displayed in the menu when you attach the app to a page.
We assume the following model::

    from django.db import models
    from django.core.urlresolvers import reverse
    import mptt

    class Category(models.Model):
        parent = models.ForeignKey('self', blank=True, null=True)
        name = models.CharField(max_length=20)

        def __unicode__(self):
            return self.name

        def get_absolute_url(self):
            return reverse('category_view', args=[self.pk])

    try:
        mptt.register(Category)
    except mptt.AlreadyRegistered:
        pass

We would now create a menu out of these categories::

    from menus.base import NavigationNode
    from menus.menu_pool import menu_pool
    from django.utils.translation import ugettext_lazy as _
    from cms.menu_bases import CMSAttachMenu
    from myapp.models import Category

    class CategoryMenu(CMSAttachMenu):

        name = _("test menu")

        def get_nodes(self, request):
            nodes = []
            for category in Category.objects.all().order_by("tree_id", "lft"):
                node = NavigationNode(
                    category.name,
                    category.get_absolute_url(),
                    category.pk,
                    category.parent_id
                )                
                nodes.append(node)
            return nodes

    menu_pool.register_menu(CategoryMenu)

If you add this menu now to your app-hook::

    from myapp.menus import CategoryMenu

    class MyApphook(CMSApp):
        name = _("My Apphook")
        urls = ["myapp.urls"]
        menus = [MyAppMenu, CategoryMenu]

You get the static entries of :class:`MyAppMenu` and the dynamic entries of
:class:`CategoryMenu` both attached to the same page.

********************
Navigation Modifiers
********************

Navigation Modifiers give your application access to navigation menus.

A modifier can change the properties of existing nodes or rearrange entire
menus.


An example use-case
-------------------

A simple example: you have a news application that publishes pages
independently of django CMS. However, you would like to integrate the
application into the menu structure of your site, so that at appropriate 
places a *News* node appears in the navigation menu.

In such a case, a Navigation Modifier is the solution.


How it works
------------

Normally, you'd want to place modifiers in your application's 
``menu.py``.

To make your modifier available, it then needs to be registered with 
``menus.menu_pool.menu_pool``.

Now, when a page is loaded and the menu generated, your modifier will
be able to inspect and modify its nodes.

A simple modifier looks something like this::

    from menus.base import Modifier
    from menus.menu_pool import menu_pool

    class MyMode(Modifier):
        """

        """
        def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
            if post_cut:
                return nodes
            count = 0
            for node in nodes:
                node.counter = count
                count += 1
            return nodes
    
    menu_pool.register_modifier(MyMode)

It has a method :meth:`~menus.base.Modifier.modify` that should return a list
of :class:`~menus.base.NavigationNode` instances.
:meth:`~menus.base.Modifier.modify` should take the following arguments:

- request

  A Django request instance. Maybe you want to modify based on sessions, or
  user or permissions?

- nodes

  All the nodes. Normally you want to return them again.

- namespace

  A Menu Namespace. Only given if somebody requested a menu with only nodes
  from this namespace.

- root_id

  Was a menu request based on an ID?

- post_cut

  Every modifier is called two times. First on the whole tree. After that the
  tree gets cut. To only show the nodes that are shown in the current menu.
  After the cut the modifiers are called again with the final tree. If this is
  the case ``post_cut`` is ``True``.

- breadcrumb

  Is this not a menu call but a breadcrumb call?


Here is an example of a built-in modifier that marks all node levels::


    class Level(Modifier):
        """
        marks all node levels
        """
        post_cut = True

        def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
            if breadcrumb:
                return nodes
            for node in nodes:
                if not node.parent:
                    if post_cut:
                        node.menu_level = 0
                    else:
                        node.level = 0
                    self.mark_levels(node, post_cut)
            return nodes

        def mark_levels(self, node, post_cut):
            for child in node.children:
                if post_cut:
                    child.menu_level = node.menu_level + 1
                else:
                    child.level = node.level + 1
                self.mark_levels(child, post_cut)
    
    menu_pool.register_modifier(Level)

**************
Custom Plugins
**************

If you want to display content of your apps on other pages custom plugins are
a great way to accomplish that. For example, if you have a news app and you
want to display the top 10 news entries on your homepage, a custom plugin is
the way to go.

For a detailed explanation on how to write custom plugins please head over to
the :doc:`custom_plugins` section.

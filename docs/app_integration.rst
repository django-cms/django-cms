App Integration
===============

It is pretty easy to integrate your own Django applications with django-cms.
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


Menus
-----

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
The get_nodes function should return a list of NavigationNode instances.
A NavigationNode takes the following arguments:

- title

  What should the menu entry read?

- url,

  Link if menu entry is clicked.

- id

  a unique id for this menu

- parent_id=None

  If this is a child of an other node give here the id of the parent.

- parent_namespace=None

  If the parent node is not from this menu you can give it the parent
  namespace. The namespace is the name of the class. In the above example that
  would be: "TestMenu"

  - attr=None

  A dictionary of additional attributes you may want to use in a modifier or
  in the template.

Attach Menus
------------

Classes that extend from `Menu` always get attached to the root. But if you
want the menu be attached to a CMS-page you can do that as well.

Instead of extending from `Menu` you need to extend from `CMSAttachMenu` and
you need to define a name. We will do that with the example from above::


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


It is encouraged to use `django-mptt <http://code.google.com/p/django-mptt/>`_
(a suitable version is included in the `mptt` directory) for the tree
structure because of performance considerations. The objects provided must
adhere to the following structure:

Each must have a ``get_menu_title`` function, a ``get_absolute_url`` function,
and a ``childrens`` array with all of its children inside (the 's' at the end
of ``childrens`` is done on purpose because ``children`` is already taken by
mptt).

Be sure that ``get_menu_title`` and ``get_absolute_url`` don't trigger any
queries when called in a template or you may have some serious performance and
DB problems with a lot of queries.

It may be wise to cache the output of ``get_nodes``. For this you may need to
write a wrapper class because of dynamic content that the pickle module can't
handle.

If you want to display some static pages in the navigation ("login", for
example) you can write your own "dummy" class that adheres to the conventions
described above.

A base class for this purpose can be found in ``cms/utils/navigation.py``




App-Hooks
---------

With App-Hooks you can attach whole Django applications to pages. For example
you have a news app and you want it attached to your news page.

To create an apphook create a cms_app.py in your application. And in there
write the following::

	from cms.app_base import CMSApp
	from cms.apphook_pool import apphook_pool
	from django.utils.translation import ugettext_lazy as _

	class MyApphook(CMSApp):
	    name = _("My Apphook")
	    urls = ["myapp.urls"]

	apphook_pool.register(MyApphook)

Replace "myapp.urls" with the path to your applications urls.py.

Now edit a page and open the advanced settings tab. Select your new apphook
under "Application". Save the page.

** ATTENTION ** If you are on a multi-threaded server (mostly all webservers,
except the dev-server): Restart the server because the URLs are cached by
Django and in a multi-threaded environment we don't know which caches are
cleared yet.

If you attached the app to a page with the url `/hello/world/` and the app has
a urls.py that looks like this:
::

	from django.conf.urls.defaults import *

	urlpatterns = patterns('sampleapp.views',
	    url(r'^$', 'main_view', name='app_main'),
	    url(r'^sublevel/$', 'sample_view', name='app_sublevel'),
	)

The 'main_view' should now be available at `/hello/world/` and the
'sample_view' has the url '/hello/world/sublevel/'.

**ATTENTION**

- All views that are attached like this must return the RequestContext besides
  the normal Context.

**Language Namespaces**

An additional feature of apphooks is that if you use the
MultilingualURLMiddleware all apphook urls are language namespaced.

What this means:

To reverse the first url from above you would use something like this in your
template::

	{% url app_main %}

If you want to access the same url but in a different language use a langauge
namespace::

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


For an example if your app has a Category model and you want this category
model to be displayed in the menu when you attach the app to a page. We assume
the following model::

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

It is encouraged to use `django-mptt <http://code.google.com/p/django-mptt/>`_
(a suitable version is included in the `mptt` directory) if you have data that
is organized in a tree.

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
	        	nodes.append(NavigationNode(category.name, category.pk, category.parent_id))
	        return nodes

	menu_pool.register_menu(CategoryMenu)

If you add this menu now to your app-hook::

	from myapp.menus import CategoryMenu

	class MyApphook(CMSApp):
	    name = _("My Apphook")
	    urls = ["myapp.urls"]
	    menus = [MyAppMenu, CategoryMenu]

You get the static entries of MyAppMenu and the dynamic entries of
CategoryMenu both attached to the same page.


Navigation Modifiers
--------------------

Navigation Modifiers can add or change properties of NavigationNodes, they
even can rearrange whole menus. You normally want to create them in your apps
menu.py.

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

It has a function modify that should return a list of NavigationNodes. Modify
should take the following arguments:

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

  Every modifier is called 2 times. First on the whole tree. After that the
  tree gets cut. To only show the nodes that are shown in the current menu.
  After the cut the modifiers are called again with the final tree. If this is
  the case post_cut is True.

- breadcrumb

  Is this not a menu call but a breadcrumb call?


Here is an example of a build in modifier that marks all nodes level::


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


Custom Plugins
--------------

If you want to display content of your apps on other pages custom plugins are
a great way to accomplish that. For example, if you have a news app and you
want to display the top 10 news entries on your homepage, a custom plugin is
the way to go.

For a detailed explanation on how to write custom plugins please head over to
the `plugins <Custom Plugins>`_ section.

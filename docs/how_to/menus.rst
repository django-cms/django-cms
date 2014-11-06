############################
Customising navigation menus
############################

In this document we discuss three different way of customising the navigation
menus of django CMS sites.

1. :ref:`integration_menus`: Statically extend the menu entries

2. :ref:`integration_attach_menus`: Attach your menu to a page.

3. :ref:`integration_modifiers`: Modify the whole menu tree

.. _integration_menus:

*****
Menus
*****

Create a ``menu.py`` in your application and write the following inside::

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

- ``title``

  What the menu entry should read as

- ``url``,

  Link if menu entry is clicked.

- ``id``

  A unique id for this menu.

- ``parent_id=None``

  If this is a child of another node supply the id of the parent here.

- ``parent_namespace=None``

  If the parent node is not from this menu you can give it the parent
  namespace. The namespace is the name of the class. In the above example that
  would be: "TestMenu"

- ``attr=None``

  A dictionary of additional attributes you may want to use in a modifier or
  in the template.

- ``visible=True``

  Whether or not this menu item should be visible.

Additionally, each :class:`NavigationNode` provides a number of methods which are
detailed in the :class:`NavigationNode <menus.base.NavigationNode>` API references.


Customize menus at runtime
==========================

To adapt your menus according to request dependent conditions (say: anonymous /
logged in user), you can use `Navigation Modifiers`_  or you can leverage existing
ones.

For example it's possible to add ``{'visible_for_anonymous': False}`` /
``{'visible_for_authenticated': False}`` attributes recognized by the
django CMS core ``AuthVisibility`` modifier.

Complete example::

    class UserMenu(Menu):
        def get_nodes(self, request):
                return [
                    NavigationNode(_("Profile"), reverse(profile), 1, attr={'visible_for_anonymous': False}),
                    NavigationNode(_("Log in"), reverse(login), 3, attr={'visible_for_authenticated': False}),
                    NavigationNode(_("Sign up"), reverse(logout), 4, attr={'visible_for_authenticated': False}),
                    NavigationNode(_("Log out"), reverse(logout), 2, attr={'visible_for_anonymous': False}),
                ]

.. _integration_attach_menus:


************
Attach Menus
************

Classes that extend from :class:`menus.base.Menu` always get attached to the
root. But if you want the menu to be attached to a CMS Page you can do that as
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

.. _integration_modifiers:

********************
Navigation Modifiers
********************

Navigation Modifiers give your application access to navigation menus.

A modifier can change the properties of existing nodes or rearrange entire
menus.


An example use-case
===================

A simple example: you have a news application that publishes pages
independently of django CMS. However, you would like to integrate the
application into the menu structure of your site, so that at appropriate
places a *News* node appears in the navigation menu.

In such a case, a Navigation Modifier is the solution.


How it works
============

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

  A Django request instance. You want to modify based on sessions, or
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
  tree gets cut to only show the nodes that are shown in the current menu.
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

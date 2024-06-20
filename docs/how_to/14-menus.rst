How to customise navigation menus
=================================

In this document we discuss three different way of customising the navigation menus of
django CMS sites.

1. :ref:`integration_menus`: Statically extend the menu entries
2. :ref:`integration_attach_menus`: Attach your menu to a page.
3. :ref:`integration_modifiers`: Modify the whole menu tree

.. _integration_menus:

Menus
-----

Create a ``cms_menus.py`` in your application, with the following:

.. code-block::

    from menus.base import Menu, NavigationNode
    from menus.menu_pool import menu_pool
    from django.utils.translation import gettext_lazy as _

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

.. note::

    Up to version 3.1 this module was named ``menu.py``. Please update your existing
    modules to the new naming convention. Support for the old name will be removed in
    version 3.5.

If you refresh a page you should now see the menu entries above. The ``get_nodes``
function should return a list of :class:`NavigationNode <menus.base.NavigationNode>`
instances. A :class:`menus.base.NavigationNode` takes the following arguments:

``title``
    Text for the menu node

``url``
    URL for the menu node link

``id``
    A unique id for this menu

``parent_id=None``
    If this is a child of another node, supply the id of the parent here.

``parent_namespace=None``
    If the parent node is not from this menu you can give it the parent namespace. The
    namespace is the name of the class. In the above example that would be: ``TestMenu``

``attr=None``
    A dictionary of additional attributes you may want to use in a modifier or in the
    template

``visible=True``
    Whether or not this menu item should be visible

Additionally, each :class:`menus.base.NavigationNode` provides a number of methods which
are detailed in the :class:`NavigationNode <menus.base.NavigationNode>` API references.

Customise menus at runtime
~~~~~~~~~~~~~~~~~~~~~~~~~~

To adapt your menus according to request dependent conditions (say: anonymous/logged in
user), you can use `Navigation Modifiers`_ or you can make use of existing ones.

For example it's possible to add ``{'visible_for_anonymous':
False}``/``{'visible_for_authenticated': False}`` attributes recognised by the django
CMS core ``AuthVisibility`` modifier.

Complete example:

.. code-block::

    class UserMenu(Menu):
        def get_nodes(self, request):
                return [
                    NavigationNode(_("Profile"), reverse(profile), 1, attr={'visible_for_anonymous': False}),
                    NavigationNode(_("Log in"), reverse(login), 3, attr={'visible_for_authenticated': False}),
                    NavigationNode(_("Sign up"), reverse(logout), 4, attr={'visible_for_authenticated': False}),
                    NavigationNode(_("Log out"), reverse(logout), 2, attr={'visible_for_anonymous': False}),
                ]

.. _integration_attach_menus:

Attach Menus
------------

Classes that extend from :class:`menus.base.Menu` always get attached to the root. But
if you want the menu to be attached to a CMS Page you can do that as well.

Instead of extending from :class:`~menus.base.Menu` you need to extend from
:class:`cms.menu_bases.CMSAttachMenu` and you need to define a name.

We will do that with the example from above:

.. code-block::

    from menus.base import NavigationNode
    from menus.menu_pool import menu_pool
    from django.utils.translation import gettext_lazy as _
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

Now you can link this Menu to a page in the *Advanced* tab of the page settings under
attached menu.

.. _integration_modifiers:

Navigation Modifiers
--------------------

Navigation Modifiers give your application access to navigation menus.

A modifier can change the properties of existing nodes or rearrange entire menus.

Example use-cases
~~~~~~~~~~~~~~~~~

A simple example: you have a news application that publishes pages independently of
django CMS. However, you would like to integrate the application into the menu structure
of your site, so that at appropriate places a *News* node appears in the navigation
menu.

In another example, you might want a particular attribute of your ``Pages`` to be
available in menu templates. In order to keep menu nodes lightweight (which can be
important in a site with thousands of pages) they only contain the minimum attributes
required to generate a usable menu.

In both cases, a Navigation Modifier is the solution - in the first case, to add a new
node at the appropriate place, and in the second, to add a new attribute - on the
``attr`` attribute, rather than directly on the ``NavigationNode``, to help avoid
conflicts - to all nodes in the menu.

How it works
~~~~~~~~~~~~

Place your modifiers in your application's ``cms_menus.py``.

To make your modifier available, it then needs to be registered with
``menus.menu_pool.menu_pool``.

Now, when a page is loaded and the menu generated, your modifier will be able to inspect
and modify its nodes.

Here is an example of a simple modifier that places each Page's ``changed_by`` attribute
in the corresponding ``NavigationNode``:

.. code-block::

    from menus.base import Modifier
    from menus.menu_pool import menu_pool

    from cms.models import Page

    class MyExampleModifier(Modifier):
        """
        This modifier makes the changed_by attribute of a page
        accessible for the menu system.
        """
        def modify(self, request, nodes, namespace, root_id, post_cut, breadcrumb):
            # only do something when the menu has already been cut
            if post_cut:
                # only consider nodes that refer to cms pages
                # and put them in a dict for efficient access
                page_nodes = {n.id: n for n in nodes if n.attr["is_page"]}
                # retrieve the attributes of interest from the relevant pages
                pages = Page.objects.filter(id__in=page_nodes.keys()).values('id', 'changed_by')
                # loop over all relevant pages
                for page in pages:
                    # take the node referring to the page
                    node = page_nodes[page['id']]
                    # put the changed_by attribute on the node
                    node.attr["changed_by"] = page['changed_by']
            return nodes

    menu_pool.register_modifier(MyExampleModifier)

It has a method :meth:`~menus.base.Modifier.modify` that should return a list of
:class:`~menus.base.NavigationNode` instances. :meth:`~menus.base.Modifier.modify`
should take the following arguments:

``request``
    A Django request instance. You want to modify based on sessions, or user or
    permissions?

``nodes``
    All the nodes. Normally you want to return them again.

``namespace``
    A Menu Namespace. Only given if somebody requested a menu with only nodes from this
    namespace.

``root_id``
    Was a menu request based on an ID?

``post_cut``
    Every modifier is called two times. First on the whole tree. After that the tree
    gets cut to only show the nodes that are shown in the current menu. After the cut
    the modifiers are called again with the final tree. If this is the case ``post_cut``
    is ``True``.

``breadcrumb``
    Is this a breadcrumb call rather than a menu call?

Here is an example of a built-in modifier that marks all node levels:

.. code-block::

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

Performance issues in menu modifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigation modifiers can quickly become a performance bottleneck. Each modifier is
called multiple times: For the breadcrumb (``breadcrumb=True``), for the whole menu tree
(``post_cut=False``), for the menu tree cut to the visible part (``post_cut=True``) and
perhaps for each level of the navigation. Performing inefficient operations inside a
navigation modifier can hence lead to big performance issues. Some tips for keeping a
modifier implementation fast:

- Specify when exactly the modifier is necessary (in breadcrumb, before or after cut).
- Only consider nodes and pages relevant for the modification.
- Perform as less database queries as possible (i.e. not in a loop).
- In database queries, fetch exactly the attributes you are interested in.
- If you have multiple modifications to do, try to apply them in the same method.

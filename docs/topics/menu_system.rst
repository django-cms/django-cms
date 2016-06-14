#########################
How the menu system works
#########################

**************
Basic concepts
**************

.. _soft-root:

Soft Roots
==========

A *soft root* is a page that acts as the root for a menu
navigation tree.

Typically, this will be a page that is the root of a significant
new section on your site.

When the *soft root* feature is enabled, the navigation menu
for any page will start at the nearest *soft root*, rather than
at the real root of the site's page hierarchy.

This feature is useful when your site has deep page hierarchies
(and therefore multiple levels in its navigation trees). In such
a case, you usually don't want to present site visitors with deep
menus of nested items.

For example, you're on the page "Introduction to Bleeding", so the menu might look like this::

    School of Medicine
        Medical Education
        Departments
            Department of Lorem Ipsum
            Department of Donec Imperdiet
            Department of Cras Eros
            Department of Mediaeval Surgery
                Theory
                Cures
                    Bleeding
                        * Introduction to Bleeding <current page>
                        Bleeding - the scientific evidence
                        Cleaning up the mess
                    Cupping
                    Leaches
                    Maggots
                Techniques
                Instruments
            Department of Curabitur a Purus
            Department of Sed Accumsan
            Department of Etiam
        Research
        Administration
        Contact us
        Impressum

which is frankly overwhelming.

By making "Department of Mediaeval Surgery" a *soft root*, the
menu becomes much more manageable::

    Department of Mediaeval Surgery
        Theory
        Cures
            Bleeding
                * Introduction to Bleeding <current page>
                Bleeding - the scientific evidence
                Cleaning up the mess
            Cupping
            Leaches
            Maggots
        Techniques
        Instruments

Registration
============

The menu system isn't monolithic. Rather, it is composed of numerous active parts, many of which can operate independently of each other.

What they operate on is a list of menu nodes, that gets passed around the menu system, until it emerges at the other end.

The main active parts of the menu system are menu *generators* and *modifiers*.

Some of these parts are supplied with the menus application. Some come from other applications (from the cms application in django CMS, for example, or some other application entirely).

All these active parts need to be registered within the menu system.

Then, when the time comes to build a menu, the system will ask all the registered menu generators and modifiers to get to work on it.

Generators and Modifiers
========================

Menu generators and modifiers are classes.

Generators
----------

To add nodes to a menu a generator is required.

There is one in cms for example, which examines the Pages in the database and adds them as nodes.

These classes are sub-classes of :py:class:`menus.base.Menu`. The one in cms is :py:class:`cms.menu.CMSMenu`.

In order to use a generator, its :py:meth:`~menus.base.Menu.get_nodes()` method must be called.

Modifiers
---------

A modifier examines the nodes that have been assembled, and modifies them according to its requirements (adding or removing them, or manipulating their attributes, as it sees fit).

An important one in cms (:py:class:`cms.menu.SoftRootCutter`) removes the nodes that are no longer required when a soft root is encountered.

These classes are sub-classes of :py:class:`menus.base.Modifier`. Examples are :py:class:`cms.menu.NavExtender` and :py:class:`cms.menu.SoftRootCutter`.

In order to use a modifier, its :py:meth:`~menus.base.Modifier.modify()` method must be called.

Note that each Modifier's :py:meth:`~menus.base.Modifier.modify()` method can be called *twice*, before and after the menu has been trimmed.

For example when using the ``{% show_menu %}`` template tag, it's called:

* first, by :py:meth:`menus.menu_pool.MenuPool.get_nodes()`, with the argument ``post_cut = False``
* later, by the template tag, with the argument ``post_cut = True``

This corresponds to the state of the nodes list before and after :py:func:`menus.templatetags.menu_tags.cut_levels()`, which removes nodes from the menu according to the arguments provided by the template tag.

This is because some modification might be required on *all* nodes, and some might only be required on the subset of nodes left after cutting.

Nodes
=====

Nodes are assembled in a tree. Each node is an instance of the :class:`menus.base.NavigationNode` class.

A NavigationNode has attributes such as URL, title, parent and children - as one would expect in a navigation tree.

It also has an ``attr`` attribute, a dictionary that's provided for you to add arbitrary attributes
to, rather than placing them directly on the node itself, where they might clash with something.

.. warning::
    You can't assume that a :py:class:`menus.base.NavigationNode` represents a django CMS Page. Firstly, some nodes may
    represent objects from other applications. Secondly, you can't expect to be able to access Page objects via
    NavigationNodes. To check if node represents a CMS Page, check for ``is_page`` in :py:attr:`menus.base.NavigationNode.attr`
    and that it is ``True``.

*****************
Menu system logic
*****************

Let's look at an example using the {% show_menu %} template tag. It will be different for other template tags, and your applications might have their own menu classes. But this should help explain what's going on and what the menu system is doing.

One thing to understand is that the system passes around a list of ``nodes``, doing various things to it.

Many of the methods below pass this list of nodes to the ones it calls, and return them to the ones that they were in turn called by.

Don't forget that show_menu recurses - so it will do *all* of the below for *each level* in the menu.

* ``{% show_menu %}`` - the template tag in the template
    * :py:meth:`menus.templatetags.menu_tags.ShowMenu.get_context()`
        * :py:meth:`menus.menu_pool.MenuPool.get_nodes()`
            * :py:meth:`menus.menu_pool.MenuPool.discover_menus()` checks every application's ``cms_menus.py``, and registers:
                * Menu classes, placing them in the ``self.menus`` dict
                * Modifier classes, placing them in the self.modifiers list
            * :py:meth:`menus.menu_pool.MenuPool._build_nodes()`
                * checks the cache to see if it should return cached nodes
                * loops over the Menus in self.menus (note: by default the only generator is :py:class:`cms.menu.CMSMenu`); for each:
                    * call its :py:meth:`menus.base.Menu.get_nodes()` - the menu generator
                    * :py:func:`menus.menu_pool._build_nodes_inner_for_one_menu()`
                    * adds all nodes into a big list
            * :py:meth:`menus.menu_pool.MenuPool.apply_modifiers()`
                * :py:meth:`menus.menu_pool.MenuPool._mark_selected()`
                * loops over each node, comparing its URL with the request.path_info, and marks the best match as ``selected``
                * loops over the Modifiers in ``self.modifiers`` calling each one's :py:meth:`~menus.base.Modifier.modify()` with ``post_cut=False``. The default Modifiers are:
                    * :py:class:`cms.menu.NavExtender`
                    * :py:class:`cms.menu.SoftRootCutter` removes all nodes below the appropriate soft root
                    * :py:class:`menus.modifiers.Marker` loops over all nodes; finds selected, marks its ancestors, siblings and children
                    * :py:class:`menus.modifiers.AuthVisibility` removes nodes that require authorisation to see
                    * :py:class:`menus.modifiers.Level` loops over all nodes; for each one that is a root node (``level == 0``) passes it to:
                        * :py:meth:`~menus.modifiers.Level.mark_levels()` recurses over a node's descendants marking their levels
        * we're now back in :py:meth:`menus.templatetags.menu_tags.ShowMenu.get_context()` again
        * if we have been provided a root_id, get rid of any nodes other than its descendants
        * :py:meth:`menus.templatetags.menu_tags.cut_levels()` removes nodes from the menu according to the arguments provided by the template tag
        * :py:meth:`menus.menu_pool.MenuPool.apply_modifiers()` with ``post_cut = True`` loops over all the Modifiers again
            * :py:class:`cms.menu.NavExtender`
            * :py:class:`cms.menu.SoftRootCutter`
            * :py:class:`menus.modifiers.Marker`
            * :py:class:`menus.modifiers.AuthVisibility`
            * :py:class:`menus.modifiers.Level`:
                * :py:meth:`menus.modifiers.Level.mark_levels()`
        * return the nodes to the context in the variable ``children``

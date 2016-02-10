##########
Navigation
##########

.. highlight:: html+django

There are four template tags for use in the templates that are connected to the
menu:

* :ttag:`show_menu`
* :ttag:`show_menu_below_id`
* :ttag:`show_sub_menu`
* :ttag:`show_breadcrumb`

To use any of these template tags, you need to have ``{% load menu_tags %}`` in
your template before the line on which you call the template tag.

.. note::

    Please note that menus live in the :mod:`menus` application, which though
    tightly coupled to the :mod:`cms` application exists independently of it.
    Menus are usable by any application, not just by django CMS.

.. templatetag:: show_menu

*********
show_menu
*********

The ``show_menu`` tag renders the navigation of the current page.
You can overwrite the appearance and the HTML if you add a ``menu/menu.html``
template to your project or edit the one provided with django CMS.
``show_menu`` takes four optional parameters: ``start_level``, ``end_level``,
``extra_inactive``, and ``extra_active``.

The first two parameters, ``start_level`` (default=0) and ``end_level``
(default=100) specify from which level the navigation should be rendered and at
which level it should stop. If you have home as a root node (i.e. level 0) and
don't want to display the root node(s), set ``start_level`` to 1.

The third parameter, ``extra_inactive`` (default=0), specifies how many levels
of navigation should be displayed if a node is not a direct ancestor or
descendant of the current active node.

The fourth parameter, ``extra_active`` (default=100), specifies how
many levels of descendants of the currently active node should be displayed.

You can supply a ``template`` parameter to the tag.

Some Examples
=============

Complete navigation (as a nested list)::

    {% load menu_tags %}
    <ul>
        {% show_menu 0 100 100 100 %}
    </ul>

Navigation with active tree (as a nested list)::

    <ul>
        {% show_menu 0 100 0 100 %}
    </ul>

Navigation with only one active extra level::

    <ul>
        {% show_menu 0 100 0 1 %}
    </ul>

Level 1 navigation (as a nested list)::

    <ul>
        {% show_menu 1 %}
    </ul>

Navigation with a custom template::

    {% show_menu 0 100 100 100 "myapp/menu.html" %}


******************
show_menu_below_id
******************

If you have set an id in the advanced settings of a page, you can display the
sub-menu of this page with a template tag. For example, we have a page called
meta that is not displayed in the navigation and that has the id "meta"::

    <ul>
        {% show_menu_below_id "meta" %}
    </ul>

You can give it the same optional parameters as ``show_menu``::

    <ul>
        {% show_menu_below_id "meta" 0 100 100 100 "myapp/menu.html" %}
    </ul>

Unlike :ttag:`show_menu`, however, soft roots will not affect the menu when
using :ttag:`show_menu_below_id`.


.. templatetag:: show_sub_menu

*************
show_sub_menu
*************

Displays the sub menu of the current page (as a nested list).

The first argument, ``levels`` (``default=100``), specifies how many levels deep
the sub menu should be displayed.

The second argument, ``root_level`` (``default=None``), specifies at what level, if
any, the menu should have its root. For example, if root_level is 0 the menu
will start at that level regardless of what level the current page is on.

The third argument, ``nephews`` (``default=100``), specifies how many levels of
nephews (children of siblings) are shown.

Fourth argument, ``template`` (``default=menu/sub_menu.html``), is the template
used by the tag; if you want to use a different template you **must** supply
default values for ``root_level`` and ``nephews``.

Examples::

    <ul>
        {% show_sub_menu 1 %}
    </ul>

Rooted at level 0::

    <ul>
        {% show_sub_menu 1 0 %}
    </ul>

Or with a custom template::

    <ul>
        {% show_sub_menu 1 None 100 "myapp/submenu.html" %}
    </ul>


***************
show_breadcrumb
***************

Show the breadcrumb navigation of the current page. The template for the HTML
can be found at ``menu/breadcrumb.html``.::

    {% show_breadcrumb %}

Or with a custom template and only display level 2 or higher::

    {% show_breadcrumb 2 "myapp/breadcrumb.html" %}

Usually, only pages visible in the navigation are shown in the
breadcrumb. To include *all* pages in the breadcrumb, write::

    {% show_breadcrumb 0 "menu/breadcrumb.html" 0 %}

If the current URL is not handled by the CMS or by a navigation extender,
the current menu node can not be determined.
In this case you may need to provide your own breadcrumb via the template.
This is mostly needed for pages like login, logout and third-party apps.
This can easily be accomplished by a block you overwrite in your templates.

For example in your ``base.html``::

    <ul>
        {% block breadcrumb %}
        {% show_breadcrumb %}
        {% endblock %}
    <ul>

And then in your app template::

    {% block breadcrumb %}
    <li><a href="/">home</a></li>
    <li>My current page</li>
    {% endblock %}



.. _extending_the_menu:


*******************************************
Properties of Navigation Nodes in templates
*******************************************
::

    {{ node.is_leaf_node }}

Is it the last in the tree? If true it doesn't have any children.

::

    {{ node.level }}

The level of the node. Starts at 0.
::

    {{ node.menu_level }}

The level of the node from the root node of the menu. Starts at 0.
If your menu starts at level 1 or you have a "soft root" (described
in the next section) the first node would still have 0 as its ``menu_level``.
::

    {{ node.get_absolute_url }}

The absolute URL of the node, without any protocol, domain or port.
::

    {{ node.title }}

The title in the current language of the node.
::

    {{ node.selected }}

If true this node is the current one selected/active at this URL.
::

    {{ node.ancestor }}

If true this node is an ancestor of the current selected node.
::

    {{ node.sibling }}

If true this node is a sibling of the current selected node.
::

    {{ node.descendant }}

If true this node is a descendant of the current selected node.
::

    {{ node.soft_root }}

If true this node is a :ref:`soft root <soft-root>`. A page can be marked as a *soft root*
in its 'Advanced Settings'.



******************************
Modifying & Extending the menu
******************************

Please refer to the :doc:`/how_to/menus` documentation

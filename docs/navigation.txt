Navigation
==========

There are four template tags for use in the templates that are connected to the menu:
``show_menu``, ``show_menu_below_id``, ``show_sub_menu``, and ``show_breadcrumb``.

show_menu
---------

``{& show_menu %}`` renders the navigation of the current page.
You can overwrite the appearance and the HTML if you add a ``cms/menu.html``
template to your project or edit the one provided with django-cms.
``show_menu`` takes four optional parameters: ``start_level``, ``end_level``,
``extra_inactive``, and ``extra_active``.

The first two parameters, ``start_level`` (default=0) and ``end_level`` (default=100) specify from what level to which level
should the navigation be rendered.
If you have a home as a root node and don't want to display home you can render the navigation only after level 1.

The third parameter, ``extra_inactive`` (default=0), specifies how many levels of navigation should be displayed
if a node is not a direct ancestor or descendant of the current active node.

Finally, the fourth parameter, ``extra_active`` (default=100), specifies how many levels of
descendants of the currently active node should be displayed.

Some Examples:
^^^^^^^^^^^^^^

Complete navigation (as a nested list)::

	{% load cache cms_tags %}
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



show_sub_menu
-------------

Display the sub menu of the current page (as a nested list).
Takes one argument that specifies how many levels deep should the submenu be displayed.
The template can be found at ``cms/sub_menu.html``::

	<ul>
    	{% show_sub_menu 1 %}
	</ul>

Or with a custom template::

	<ul>
		{% show_sub_menu 1 "myapp/submenu.html" %}
	</ul>

show_breadcrumb
---------------

Show the breadcrumb navigation of the current page.
The template for the HTML can be found at ``cms/breadcrumb.html``.::

	{% show_breadcrumb %}

Or with a custom template and only display level 2 or higher::

	{% show_breadcrumb 2 "myapp/breadcrumb.html" %}

If the current URL is not handled by the CMS or you are working in a navigation extender,
you may need to provide your own breadcrumb via the template.
This is mostly needed for pages like login, logout and third-party apps.


.. _extending_the_menu:


Properties of Navigation Nodes in templates
-------------------------------------------
::

	{{ node.is_leaf_node }}

Is it the last in the tree? If true it doesn't have any children.
(This normally comes from mptt.)
::

	{{ node.level }}

The level of the node. Starts at 0.
::

	{{ node.menu_level }}

The level of the node from the root node of the menu. Starts at 0.
If your menu starts at level 1 or you have a "soft root" (described
in the next section) the first node still would have 0 as its `menu_level`.
::

	{{ node.get_absolute_url }}

The absolute URL of the node.
::

	{{ node.get_title }}

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

If true this node is a "soft root".

Soft Roots
----------

"Soft roots" are pages that start a new navigation.
If you are in a child of a soft root node you can only see the path to the soft root.
This feature is useful if you have big navigation trees with a lot of pages and don't
want to overwhelm the user.

To enable it put the following in your ``settings.py`` file::

	CMS_SOFTROOT = True

Now you can mark a page as "soft root" in the 'Advanced' tab of the page's settings in the admin interface.


Modifying & Extending the menu
------------------------------

Please refer to the app integration documentation

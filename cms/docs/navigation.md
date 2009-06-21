Navigation
==========

There are 4 template tags for use in the templates that are connected to the menu:

show\_menu
---------

show\_menu renders the navigation of the current page.
You can overwrite the appearance and the HTML if you add a cms/menu.html template to you project or edit the one provided with django-cms.
show\_menu takes 4 parameters:

From what level to which level of the navigation should the navigation be rendered?

**start\_level** (default=0)
**end\_level** (default=100)

If you have a home as a root node and don't want to display home you can render the navigation only after level 1:

**extra\_inactive** (default=0)

If a node is not a direct ancestor or descendant of the current active node, how many levels deep should the navigation be displayed?

**extra\_active** (default=100)

If a node is currently active, how many levels deep should its descendants be displayed?

Some Examples:

Complete navigation (as a nested list):

	{% load cache cms_tags %}
	<ul>
		{% show_menu 0 100 100 100 %}
	</ul>

Navigation with active tree (as a nested list):

	<ul>
		{% show_menu 0 100 0 100 %}
	</ul>

Navigation with only one active extra level:

	<ul>
		{% show_menu 0 100 0 1 %}
	</ul>

Level 1 navigation (as a nested list):

	<ul>
		{% show_menu 1 %}
	</ul>

Navigation with a custom template:

	{% show_menu 0 100 100 100 "myapp/menu.html" %}
	
	
show\_menu\_below\_id
---------------------

If you have a set an id in the advanced settings of a page, you can display the submenu of this page with
a template tag.  For example, we have a page called meta that is not displayed in the navigation and that
has the id "meta":

	<ul>
		{% show\_menu\_below\_id "meta" %}
	</ul>

You can give it the same parameters as show\_menu as well:

	<ul>
		{% show\_menu\_below\_id "meta" 0 100 100 100 "myapp/menu.html" %}
	</ul>


show\_sub\_menu
---------------

Display the sub menu of the current page (as a nested list).
Takes one argument: how many levels deep should the submenu be displayed?
The template can be found at cms/sub_menu.html:

	<ul>
    	{% show\_sub\_menu 1 %}
	</ul>

Or with a custom template:

	<ul>
		{% show\_sub\_menu 1 "myapp/submenu.html" %}
	</ul>

show\_breadcrumb
---------------

Show the breadcrumb navigation of the current page.
The template for the HTML can be found at cms/breadcrumb.html.

	{% show\_breadcrumb %}

Or with a custom template:

	{% show\_breadcrumb "myapp/breadcrumb.html" %}

If the current URL is not handled by the CMS or you are working in a navigation extender,
you may need to provide your own breadcrumb via the template.
This is mostly needed for pages like login, logout and third-party apps.
A global solution for this problem for Django would be much appreciated.


Extending the menu
------------------

The menu can be extended with static or dynamic content.
For example, you may have a shop with categories and want these categories to be displayed in the navigation.

Add the following to your settings file:

	CMS_NAVIGATION_EXTENDERS = (('myapp.utils.get_nodes', gettext('Shop Categories')),)

Now you can link a navigation extender to a page in the 'Advanced' tab of the page settings.

An example of an extender function is in utils.py in myapp:

	from categories.models import Category
	
	def get_nodes(request):
		categories = list(Category.objects.all())
		res = [] # result list
		all_categories = categories[:]
		children = [] # all categories with a parent

		# put all of the child categories in a list of their
		# own (children) and add all of the parent categories
		# (that is, categories with no parent) to the result list
	    	for category in categories:
	        	if category.parent_id:
                                # this is a child category
				children.append(category)
			else:
				# this is a parent category
				res.append(category)

		for category in all_categories:
			category.children = []
			for child in children:
				if child.parent_id == category.pk:
					category.children.append(child)
		return res
    
The model would look something like this:

	from django.db import models
	from django.core.urlresolvers import reverse
	import mptt
	
	class Category(models.Model):
		parent = models.ForeignKey('self', blank=True, null=True)
		name = models.CharField(max_length=20)
	
	def __unicode__(self):
		return self.name
	
	def get_title(self):
		return self.name
	
	def get_absolute_url(self):
		return reverse('category_view', args=[self.pk])
	
	try:
		mptt.register(Category)
	except mptt.AlreadyRegistered:
		pass
    
It is encouraged to use mptt for the tree structure because of performance considerations.
The objects provided must adhere to the following structure:

Each must have a get\_title function, a get\_absolute\_url function, and a
childrens* array with all of its children inside (the s at the end of 'childrens' is done on purpose
because children is already taken by mptt).

Be sure that get\_title and get\_absolute\_url don't trigger any queries when called in a template or you 
may have some serious performance and DB problems with a lot of queries.

It may be wise to cache the output of get_nodes. For this you may need to write a wrapper class because of
dynamic content that the pickle class can't handle.

If you want to display some static pages in the navigation ("login", for example) you can write your own "dummy" class that adheres to the conventions described above.

Properties of Navigation Nodes in templates
----------------------------------------------

	{{ node.is_leaf_node }}

Is it the last in the tree? If true it doesn't have any children.
(This normally comes from mptt.)

	{{ node.level }}

The level of the node. Starts at 0.

	{{ node.menu_level }}
	
The level of the node from the root node of the menu. Starts at 0.
If your menu starts at level 1 or you have a soft\_root the first node still would have 0 as its menu\_level.

	{{ node.get_absolute_url }}

The absolute url of the node.

	{{ node.get_title }}

The title in the current language of the node.

	{{ node.selected }}

If true this node is the current one selected/active at this URL.
 
	{{ node.ancestor }}

If true this node is an ancestor of the current selected node.

	{{ node.sibling }}

If true this node is a sibling of the current selected node.

	{{ node.descendant }}

If true this node is a descendant of the current selected node.

	{{ node.soft_root }}

If true this node is a "softroot".

Softroot
--------

Softroots are pages that start a new navigation.
If you are in a child of a softroot node you can only see the path to the softroot.
This feature is useful if you have big navigation trees with a lot of sites and don't want to overwhelm users.

To enable it put the following in your settings.py file:

	CMS\_SOFTROOT = True

Now you can mark a page as softroot in the 'Advanced' tab of the page's settings in the admin interface.

page\_id\_url
-----------

This template tag returns the URL of a page that has a symbolic name, known as
a reverse\_id.  For example, you could have a help page that you want to display a link to 
on every page.  To do this, you would go to the help page in the admin sent and
enter a reverse id (such as "help") in the 'Advanced' tab of the page's settings.
You could then obtain a URL for the help page in a template like this:

	<a href="{% page_id_url "help" %}">help</a>

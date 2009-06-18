Navigation
==========

There are 4 templatetags for use in the templates that are connected to the menu:

show_menu
---------

show\_menu renders the navigation of the current page.
You can overwrite the appearance and the html if you add a cms/menu.html template to you project or edit the one provided with django-cms
show\_menu takes 4 parameters:
from what level of the navigation to which level should the navigation be rendered?

**start\_level** (default=0)  
**end\_level** (default=100)

if you have a home as a root node and don't want to display home you can render the navigation only after level 1

**extra\_inactive** (default=0)

if a node is not a direct ancestor or descendant of the current active node how many levels deep should the navigation be displayed?

**extra\_active** (default=100)

if a node is the current active, how many levels deep should its descendants be displayed?

Some Examples:

Complete navigation (as a nested list)

	{% load cache cms_tags %}
	<ul>
		{% show_menu 0 100 100 100 %}
	</ul>

Navigation with active tree(as a nested list)

	<ul>
		{% show_menu 0 100 0 100 %}
	</ul>

Navigation with only 1 active extra level

	<ul>
		{% show_menu 0 100 0 1 %}
	</ul>

Level 1 navigation (as a nested list)

	<ul>
		{% show_menu 1 %}
	</ul>

Navigation with own template:

	{% show_menu 0 100 100 100 "myapp/menu.html" %}
	
	
show\_menu\_below\_id
---------------------

If you have a set an id in the advanced settings of a page you can display the submenu of this page with
a template tag:

For example we have a page called meta that is not displayed in the navigation and that has the id "meta"

	<ul>
		{% show\_menu\_below\_id "meta" %}
	</ul>

You can give it the same parameters as show\_menu as well:

	<ul>
		{% show\_menu\_below\_id "meta" 0 100 100 100 "myapp/menu.html" %}
	</ul>


show\_sub\_menu
---------------

Display the sub menu of the current page (as a nested list)
Takes one argument: how many levels deep should the submenu be displayed?
The template can be found at cms/sub_menu.html

	<ul>
    	{% show\_sub\_menu 1 %}
	</ul>

with your own template:

	<ul>
    	{% show_sub_menu 1 "myapp/submenu.html" %}
	</ul>

show_breadcrump
---------------

Show the breadcrumb navigation of the current page
The tamplate for the html can be found at cms/breadcrumb.html

	{% show_breadcrumb %}

with your own template:

	{% show_breadcrumb "myapp/breadcrumb.html" %}

If the current url is not handled by the cms or i a navigation extender you may need to provide your own breadcrump via the template.
This is mostly needed for pages like login, logout and 3th party apps.

A global solution for this problem for django would be welcome


Extending the menu
------------------

There is a way to extend the menu with static or dynamic content.
For example you have a shop with categories and want these categories to be displayed in the navigation.

Add the following to your settings file:

	CMS_NAVIGATION_EXTENDERS = (('myapp.utils.get_nodes', gettext('Shop Categories')),)

Now you are able to link a Navigation Extender to a page in the Advanced Tab of the Page Settings.

An example of an extender function in a utils.py in myapp:

	from categories.models import Category

	def get_nodes(request):
    	cats = list(Category.objects.all())
    	res = []
    	all_cats = cats[:]
    	childs = []
    	for cat in cats:
        	if cat.parent_id:
            	childs.append(cat)
        	else:
            	res.append(cat)
    	for cat in all_cats:
        	cat.childrens = []
        	for child in childs:
            	if child.parent_id == cat.pk:
                	cat.childrens.append(child)
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
The objects provided must adhere to the following Structure:

they must have a:

get_title function
get\_absolute\_url function
childrens array with all its children inside (the s at the end is done on purpose because children is already taken by mptt)

Be sure that get\_title and get\_absolute\_url doesn't trigger any queries when called in the template or otherwise you 
may have some serious performance and DB problems with lot of queries

It may be wise to cache the output of get_nodes. For this you may need to write a wrapper Class because of dynamic content the pickle class can't handle
If you want to display some static pages in the navigation like "login" for example you can write your own DummyClass that adheres to the standards from above.

Properties of Navigation Nodes in the template
----------------------------------------------

	{{ node.is_leaf_node }}

Is it the last in the tree? If true it doesn't have any children
Comes normally from mptt

	{{ node.level }}

The level of the node. Starts at 0

	{{ node.menu_level }}
	
The level of the node from the root node of the menu. Starts at 0
If your menu starts at level 1 or you have a soft\_root the first node still would have 0 as menu\_level

	{{ node.get_absolute_url }}

The absolute url of the node

	{{ node.get_title }}

The title in the current language of the node

	{{ node.selected }}

If true this node is the current selected/active at this URL
 
	{{ node.ancestor }}

If true this node is an ancestor of the current selected node.

	{{ node.sibling }}

If true this node is a sibling of the current selected node.

	{{ node.descendant }}

If true this node is a descendant of the current selected node.

	{{ node.soft_root }}

If true this node is softroot

Softroot
--------

Softroots are pages that start a new navigation.
If you are in a child of a softroot node you can only see the path to the softroot.
This feature is useful if you have big navigation trees with a lot of sites and don't want to overwhelm the user

To enable it put the following to your settings.py

	CMS_SOFTROOT = True

Now you can mark a page as softroot in the advanced Tab of the Page Settings.

page\_id\_url
-----------

This templatetag return the url of a page that has reverse_id.
If you have for example a help page and want to display a link to this site from every page:

Goto this page in the admin and enter a reverse_id in the advanced tab.

Example: "help"

now you can place the page\_id\_url in your template like this.

	<a href="{% page_id_url "help" %}">help</a>


 


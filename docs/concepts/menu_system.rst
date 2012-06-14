#########################
How the menu system works
#########################

**************
Basic concepts
**************

Registration
============

The menu system isn't a monolithic structure. Rather, it is composed of numerous active parts, many of which can operate independently of each other.

These parts are menu *generators* and *modifiers*.

Some of these parts are supplied with the menus application. Some come from from other applications (from the cms application in django CMS, for example, or some other application entirely).

All these active parts need to be registered with the menu system.

Then, when the time comes to build a menu, the system will ask all the registered menu generators and modifiers to get to work on it.

Generators and Modifiers
======================== 

Menu generators and modifiers are classes.

Generators
----------

To add nodes to a menu a generator is required. 

There is one is cms for example, which examines the Pages in the database and adds them as nodes.

These classses are subclasses of menus.base.Menu. The one in cms is cms.menu.CMSMenu.

In order to use a generator, its get_nodes() method must be called.

Modifiers
---------

A modifier examines the nodes that have been assembled, and modifies them according to its requirements (adding or removing them, or manipulating their attributes, as it sees fit).

One important one in cms removes the nodes that are no longer required when a soft root is encountered.

These classes are subclasses of menus.base.Modifier. Examples are cms.menu.NavExtender and cms.menu.SoftRootCutter.

In order to use a modifier, its modify() method must be called.
            
Note that each Modifer's modify() method can be called *twice*, before and after the menu has been trimmed.

For example when using the {% show_menu %} templatetag, it's called: 

* first, by menu_pool.MenuPool.get_nodes(), with the argument post_cut = False
* later, by the templatetag, with the argument post_cut = True

This corresponds to the state of the nodes list before and after menus.templatetags.cut_levels(), which removes nodes from the menu according to the arguments provided by the templatetag.

This is because some modification might be required on *all* nodes, and some might only be required on the subset of nodes left after cutting.

Nodes
=====

Nodes are assembled in a tree. Each node is an instance of the menus.base.NavigationNode class.

Aa NavigationNode has attributes such as URL, title, parent and children - as one would expect in a navigation tree.

***********************
How does all this work?
***********************

Tracing the logic of the menu system
====================================

Let's look at an example using the {% show_menu %} templatetag. 

Each of the methods below passes a big list of nodes to the ones it calls, and returns them to the one that it was in turn called by.
                 
Don't forget that show_menu recurses - so it will do all of the below for each level in the menu.

* {% show_menu %} # the templatetag in the template
    * menu_tags.ShowMenu.get_context() 
        * menu_pool.MenuPool.get_nodes()
            * menu_pool.MenuPool.discover_menus() # checks every application's menu.py, and registers:
 				* unregistered Menu classes, placing them in the self.menus dict
				* unregistered Modifier classes, placing them in the self.modifiers list
            * menu_pool.MenuPool._build_nodes() 
                * checks the cache to see if it should return cached nodes
                * loops over the Menus in self.menus (note: by default the only generator is cms.menu.CMSMenu); for each:
				    * call its get_nodes() # the menu generator
				    * calls menu_pool._build_nodes_inner_for_one_menu(), add all nodes into a big list
            * menu_pool.MenuPool.apply_modifiers() 
                * menu_pool.MenuPool._mark_selected() # loops over each node, comparing its URL with the request.path, and marks the best match as `selected`
                * loops over the Modifiers in self.modifiers calling modify(post_cut = False) # default Modifiers are:
                    * cms.menu.NavExtender
                    * cms.menu.SoftRootCutter 
                    * menus.modifiers.Marker # loops over all nodes; finds selected, marks its ancestors, siblings and children
                    * menus.modifiers.AuthVisibility # removes nodes that require authorisation
                    * menus.modifiers.Level # loops over all nodes; for each one that is a root node (level = 0) passes it to:
                        * menus.modifiers.Level.mark_levels() # recurses over a node's descendants marking their levels
    * back in menu_tags.ShowMenu.get_context() again
    * if we have been provided a root_id, get rid of any nodes other than its descendants
    * menus.templatetags.cut_levels() # removes nodes from the menu according to the arguments provided by the templatetag
    * menu_pool.MenuPool.apply_modifiers(post_cut = True) # I won't list them all again
    * return the nodes to the context
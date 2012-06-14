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

In the representation below, an blank line separates methods. An indentation reflects a similar Python/logical indentation.

Each of the methods below passes a big list of nodes to the ones it calls, and returns them to the one that it was in turn called by.
                 
Don't forget that show_menu recurses - so it will do all of the below for each level in the menu.

    {% show_menu %}: # the templatetag in the template

        menu_tags.ShowMenu.get_context():

            menu_pool.MenuPool.get_nodes():

                menu_pool.MenuPool.discover_menus():
                    # this loops over every application, checking the menu.py file; it registers:
     				* 	unregistered Menu classes, placing them in the self.menus dict
    				*	unregistered Modifier classes, placing them in the self.modifiers list]

                menu_pool.MenuPool._build_nodes():
                    [this first checks the cache to see if it should return cached nodes]

                    [then, it loops over the Menus in self.menus - by default the only one is:
                    *   cms.menu.CMSMenu]:
                
    				cms.menu.CMSMenu.get_nodes() [the menu's own method for getting nodes]

    				menu_pool._build_nodes_inner_for_one_menu() [I don't really understand what this does]

    				adds all nodes into a big list
                        ]

                menu_pool.MenuPool.apply_modifiers(): 

                    menu_pool.MenuPool._mark_selected():
                        [loops over each node, comparing its URL with the request.path, and marks the best match as selected]

                    [loops over the Modifiers in self.modifiers - by default, these are:
                    *   cms.menu.NavExtender
                    *   cms.menu.SoftRootCutter 
                    *   menus.modifiers.Marker
                    *   menus.modifiers.AuthVisibility
                    *   menus.modifiers.Level]:
                
                        cms.menu.NavExtender.modify() [needs a description]
                    
                        cms.menu.SoftRootCutter.modify() [needs a description]
                    
                        menus.modifiers.Marker.modify():
                            loops over all nodes
                                once it has found the selected node, marks all its ancestors, siblings and children
                    
                        menus.modifiers.AuthVisibility.modify() [removes nodes that require authorisation]
                    
                        menus.modifiers.Level.modify():
                            if post_cut = False, loops over all nodes; for each one that is a root node (level = 0) passes it to:

                                menus.modifiers.Level.mark_levels(): 
                                    [recurses over a node's descendants marking their levels until it has reached them all]

            [we are now back in menu_tags.ShowMenu.render() again]
            if we have been provided a root_id, get rid of any nodes other than its descendants]
        
            menus.templatetags.cut_levels() [removes nodes from the menu according to the arguments provided by the templatetag]
        
            menu_pool.MenuPool.apply_modifiers(post_cut = True) [remember we did these earlier with post_cut = False]
    
            returns the nodes to the context
##############
Adding plugins
##############

In this section we will edit the *How to find us* page to show a map, using a *plugin*.


*************
About plugins
*************

There are django CMS for all kinds of purposes, but whatever the content they place into your page
the principle is the same: it allows you to publish and manage an almost infinite variety of
content with a very simple interface.

Plugins can publish:

* a map
* text
* an image
* a gallery
* an automatic list of news or events items

... and much, much more.

The plugin architecture means that django CMS can be kept simple and lightweight, with the
multitude of plugins being made available by other compatible applications that you can easily
install if you want them.


***************************
Structure and content modes
***************************

.. image:: /user/tutorial/images/structure-content.png
     :align: right
     :alt: the 'Structure/Content' mode control
     :width: 148

The *Structure/Content* mode control in the toolbar lets you switch between two different editing
modes.

You've already used *Content* mode, in which you can double-click on content to edit it.

In *Structure* mode, you can manage the placement of content within the page structure.

.. |structure-button| image:: /user/tutorial/images/structure-button.png
   :alt: 'structure'
   :width: 148

* Switch to *Structure* mode by hitting the |structure-button| button.

This reveals the *structure board* containing the *placeholders* available on the page, and the
*plugins* in them. Here you can see just one placeholder, called *Content*, containing one plugin -
a text plugin that begins *Our workshop is at Zollstrasse 53...*.

.. image:: /user/tutorial/images/structure-board.png
     :alt: the structure board


Add a second plugin
===================

Let's add another plugin, containing a map.

#.  Select the **Add plugin** icon.

    .. image:: /user/tutorial/images/add-plugin-icon.png
       :alt: 'add plugin'
       :width: 300

#.  Choose *Google Map* from the list of available plugin types.

    .. image:: /user/tutorial/images/google-map-plugin.png
         :alt: the list of plugin types
         :width: 400

    This will open a new dialog box, in which you can provide some basic details for your map.

#.  Add the details and **Save**.

    .. tip::

        Map title
            Our workshop

        Address
            Zollstrasse 53

        Zip code
            8001

        City
            Zürich


Now in the structure board you'll see the new *Google Map* plugin.

Each plugin in the structure board is available for editing by double-clicking or by tapping the
edit icon.

.. image:: /user/tutorial/images/structure-board-with-two-plugins.png
   :alt: the structure board with two plugins

You can move these plugins around to change their relative position, if you wish, or even to
another placeholder, simply by dragging them.

.. note::

    Remember, any changes you make will need to be published in order for other users to see them.

You can switch back to content mode to see the effect of your changes.

.. image:: /user/tutorial/images/page-with-google-map.png
   :alt: the Google Maps plugins shows the workshop location

* **Publish** the page to make your new changes and the map public.

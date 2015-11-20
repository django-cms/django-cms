##############
Adding plugins
##############

In this section we will edit the *How to find us* page to show a map, using a *plugin*.


***************************
Structure and content modes
***************************

.. image:: /user/tutorial/images/structure-content.png
     :align: right
     :alt: the 'Structure/Content' mode control
     :width: 71

The *Structure/Content* mode control in the toolbar lets you switch between two different editing
modes.

You've already used *Content* mode, in which you can double-click on content to edit it.

In *Structure* mode, you can manage the placement of content within the page structure.

.. todo:: add a structure button image as structure-button.png

.. |structure-button| image:: /user/tutorial/images/structure-button.png
   :alt: 'structure'

* Switch to *Structure* mode by hitting the |structure-button| button.

This reveals the *structure board* containing the *placeholders* available on the page, and the
*plugins* in them:

.. image:: /user/tutorial/images/structure-board.png
     :align: right
     :alt: the structure board

Here there is just one placeholder, called *Content*, containing one plugin - a text plugin that
begins *Our workshop is at Zollstrasse 53...*.

.. image:: /user/tutorial/images/add-plugin.png
     :alt: the 'Add plugin' icon
     :width: 308


Add a second plugin
===================

Let's add another plugin, containing a map.

.. todo:: add the "Add plugin" icon as add-plugin.png

.. |add-plugin-icon| image:: /user/tutorial/images/add-plugin-icon.png
   :alt: 'add plugin'

#.  Select the **Add plugin** icon |add-plugin-icon|.
#.  Choose *Google Map* from the list of available plugin types.

    .. todo:: replace the image, with one showing Google Map in the list

    .. image:: /user/tutorial/images/text-plugin.png
         :alt: the list of plugin types
         :width: 165

    This will open a new dialog box, in which you can provide some basic details for your map.

#.  Add the details and **Save**.

    .. tip::

        Map title
            Our workshop

        Address
            Zollstrasse 53

        Zip code
            ??????????????? Dario can you check?

        City
            Zürich


Now in the structure board you'll see the new *Google Map* plugin - which you can move around
within the structure by dragging, to re-order the plugins so that it comes before or after the
*Text* plugin you created earlier.

Each plugin in the structure board is available for editing by double-clicking or by tapping the
edit icon.

.. image:: /user/tutorial/images/structure-board-with-two-plugins.png
   :alt: the structure board with two plugins

.. note::

    As ever, any changes you make will need to be published in order for other users to see them.

You can switch back to content mode to see the effect of your changes.

.. todo:: screenshot of the page showing the map

* **Publish** the page to make your new changes and the map public.


*************
About plugins
*************

There are django CMS for all kinds of purposes, but whatever the content they place into your page
(it could be a map, text, an image, a gallery, an automatic list of news or events items - and
more), the principle is the same: it allows you to publish and manage an almost infinite variety of
content with a very simple interface.

The plugin architecture means that django CMS can be kept simple and lightweight, with the
multitude of plugins being made available by other compatible applications that you can easily
install if you want them.

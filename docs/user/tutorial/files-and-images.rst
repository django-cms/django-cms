#############################
Working with files and images
#############################

You'll often need to include files, such as image files, PDFs and so on, in your content management
work. Django Filer is an ideal way to store, retrieve and manage these files. Like Aldryn News &
Blog, it's not part of django CMS, but integrates with it extremely well and is strongly
recommended for any site.


===============
Change an image
===============

.. image:: images/image_hover.png
   :alt: Double-click to edit an image
   :align: right
   :width: 25%

To explore the basic use of Django Filer, we'll start by changing an existing image. Find an image
in a page, and hover over it in *Draft mode* - you'll see the indicator that shows this is an
*Image*.

Double-click to open the plugin.

You can change such things as the image's ``Title``, but you can also change the image itself.

.. |search| image:: images/search.png
   :width: 5%

Select the **search** icon (|search|) next to the thumbnail image. Navigate through the
folder structure to find a suitable image. You can also search for files by name.

When you have found a file you'd like to use, hit the **Select this file** icon on its left.

.. image:: images/select_file.png
   :alt: The 'Select file' icon

**Save**, and the new image will be used in place of the existing one.


============================
Add a new image to the Filer
============================

If a suitable image does not already exist in the Filer, you can add a new one.

.. |upload| image:: images/upload.png
   :alt: The 'Upload' button
   :width: 10%

Open the plugin as before, hit the **search** icon, and then the **Upload** button |upload|.

Chose an image - or multiple images - from your local drive. After a few moments for processing,
they will appear on the *Clipboard*.

.. figure:: images/past_image.png
   :alt: The 'Paste' icon
   :align: right
   :figwidth: 25%

   ..

   The **Paste** icon


Navigate to the folder where you want to place these files, then hit the **Paste** icon to move
them from the *Clipboard* to the folder.

.. figure:: images/move_clipboard.png
   :alt: The 'Move to Clipboard' icon
   :align: right
   :figwidth: 25%

   ..

   The **Move to Clipboard** icon

You can also move items to the clipboard using the **Move to clipboard** icon, and also discard
items from the *Clipboard* if required.

Now you can select the image to use for the plugin as you did before, and **Save** the plugin.


===================================
Using the Filer in the Django Admin
===================================

.. image:: images/admin_nav.png
   :alt: Navigating to the Django admin
   :align: right
   :width: 40%

So far we have got into the Filer via an image plugin, but sometimes it's convenient to get there
directly.

In the Toolbar, select the *Site menu* and choose *Administration*.

.. image:: images/zoom_panel.png
   :alt: The zoom button
   :align: right
   :width: 10%

Expand the Admin view by hitting the sidepane's **Zoom button**. In the *Filer* section select
*Folders*, where you can explore the folder structure, and use the Filer interface as before.

.. image:: images/admin_site.png
   :alt: The admin site
   :width: 40%

=============================
Editing an image in the Filer
=============================

Locate the image you added to the Filer earlier, and hit its thumbnail icon there.

.. image:: images/thumbnail-photo.png
   :alt: Image thumbnail icons in the Filer
   :width: 60%

Now you can edit the file's settings, such as ``Name``, ``Description`` and ``Author`` - change
them appropriately.

.. image:: images/red-dot.png
   :alt: The image focus control
   :align: right
   :width: 60%

Choose the image's *focus point* - the point around which any cropping will occur - by dragging the
red circle in the image pane.

This helps ensure for example that however a portrait is cropped, the subject's head will not be
chopped off. If your image doesn't have a particular focus point, leave the circle in the middle of
the image.

**Save** the image.

Note that if you change the focus point, any examples of that image already in your pages will
change automatically.


=======================================
Insert an Image plugin in a Text plugin
=======================================

Open a Text plugin by double-clicking on it, as you did in :ref:`edit_some_text` above. Place the
cursor at the point where you want the image to be inserted, and select *Image* from the *CMS
Plugins* menu.

The *Add Filer image* dialog will open.

.. image:: images/text-image-plugin.png
   :alt: 'Image' in the CMS Plugins menu
   :align: right
   :width: 60%

You can add an optional caption, or set some of the additional options, and when ready, hit **OK**
to insert the image into the text plugin.

Once you **Save** the text plugin, you'll be able to see the image in your page.

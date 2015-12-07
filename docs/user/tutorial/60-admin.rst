################
The Django Admin
################

******************
The Admin overlay
******************

Open the overlay
================

.. image:: images/admin_nav.png
   :alt: Navigating to the Django admin
   :align: right
   :width: 40%

In the Toolbar, select the *Site menu* and choose *Administration*.

This opens the django CMS *overlay*, which provides a quick view onto some extra control
functionality.

Each application in the system has its own set of entries.

.. image:: images/zoom_panel.png
   :alt: The zoom button
   :width: 100%


Add an image to the Filer
=============================

#.  Find the *Django Filer* application in the list.

    .. image:: images/admin_site.png
       :alt: The admin site

#.  Select *Folders*.

    .. |new-folder| image:: images/new_folder_button.png
       :alt: the 'New folder' button
       :width: 130px

#.  When the Filer opens, select |new-folder|.

#.  Name the new folder *People*, and hit **Save**.

#.  Find the new folder in the list and select it to open it.

    .. |upload_button| image:: images/upload_button.png
       :alt: The upload button

#.  Now we want to upload a new image: hit |upload_button|, and select a suitable image (JPEG,
    PNG and GIF files are recommended) from your hard disk. The image(s) you upload will be placed
    on the *clipboard*.

    .. image:: images/clipboard.png
      :alt: the clipboard

    .. |image_paste| image:: images/image_paste.png
       :alt: the 'Paste' icon

#.  Add the images to the folder, by selecting |image_paste|.

Now you have a image in the Filer, that you can reuse anywhere you need to. If you change the image,
every instance where you've used it will also be updated, potentially saving you a lot of time and
effort when images need to be updated.


**************************
Managing files and folders
**************************

Editing items
=============

You can edit a file's details at any time by selecting it.

#.  Select the image in the Filer that you want to edit.

#.  Change its *Name* and *Description* and any other fields you'd like to edit.

    .. image:: images/image_description.png
       :alt: the Edit image dialog

#.  Select the image's *focus point* - the point around which any cropping will occur - by dragging
    the red circle in the image pane.

    .. image:: images/image_focus.png
        :alt: the focus point control
        :width: 40%
        :align: center

    This helps ensure for example that however a portrait is cropped, the subject's head will not be
    chopped off. If your image doesn't have a particular focus point, leave the circle in the middle
    of the image.

    Note that if you change the focus point, any examples of that image already in your pages will
    change automatically.

#.  **Save** your changes.


Moving items
============

You can manage your images and files, by moving them around within folders, creating a folder structure that suits your needs and so on.

Let's move a file.

#.  Start by selecting the image you want to move.

    .. |cut| image:: images/cut.png
       :alt: the 'Cut' icon
       :width: 48

#.  Move it to the clipboard, using the |cut| icon.

#.  Navigate back up the folder hierarchy to the *Root* folder, by using the *move back* icon in
    the Filer. You can also select a folder in the path from the breadcrumb trail just above it.

    .. image:: images/breadcrumb.png
       :alt: Breadcrumb

    .. image:: images/back_to_root_file.png
       :alt: Moving up in the folder hierarchy
       :align: center

#.  Create a new folder called *Staff*, as you did previous, and open it.

#.  Once more, use |image_paste| to place the file in the new folder.


Using images from the Filer
===========================

Now that you have added an image to the Filer, it's easy to use it - and reuse it - whenever you
need.

.. |close_admin| image:: images/close_admin.png
   :alt: the 'close' icon of the admin overlay

#.  Close the admin overlay, by hitting the |close_admin| icon in its top right-hand corner.

#.  Go to the *People* page on the site.

#.  From the django CMS toolbar, select *People* > *Person* list.

    .. image:: images/person_list.png
       :alt: showing person list

#.  Choose the Person you want to edit from the list.

#.  Hit the "choose image" icon.

    .. image:: images/choose_image.png
       :alt: showing person list

#.  The Filer will open; find the image you want to use for this Person.

#.  To apply the image to the Person, hit the "select this file"" icon

    .. image:: images/select_file.png
       :alt: showing person list

#.  Save the Person, and see your changes.

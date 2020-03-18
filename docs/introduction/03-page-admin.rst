##########
Page admin
##########

.. _toolbar:

**********************
The django CMS toolbar
**********************

The toolbar is central to your content editing and management work in django
CMS. Take a few monents to explore the items in the toolbar. Key items from left to right are (note that some items are only available in
*Edit* mode):

.. figure:: /introduction/images/toolbar.png

* *django CMS* - takes you back to home page of your site
* the *Site* menu, labelled with the site's name (here, *example.com*) - contains options for site-level administration
* the *Page* menu - contains options for managing the current page
* the *Language* menu - allows you to switch to a different language version of the page you're on, and manage the various translations
* **undo**/**redo** buttons
* **Create** new content
* **View published** - switch to the published version of the page when in Edit mode
* the **Structure mode** button - displays placeholders and plugins


.. _page-list:

**********************
Page list
**********************

The *page list* (*Site* > *Pages...*) gives you an overview of your pages and their status.

.. figure:: /introduction/images/page-list.png

The table shows the publishing state of each translation (empty disk: no content, grey disk: unpublished; blue disk: has unpublished edits;
green: fully published).

It also shows which pages are home pages and soft roots, and which have applications attached (see :ref:`apphooks_introduction` later in this
tutorial).

Pages can be moved around in the hierarchy by dragging.


.. _basic-page-settings:

**********************
Basic page settings
**********************

.. figure:: /images/page-basic-settings.png
   :figwidth: 300
   :align: right

To see a page's basic settings, select *Page settings...* from the *Page* menu.

Try changing some of the fields to see their effect:

* *Title*, typically used by a site's templates, and displayed at the top of the page and in the browser's title bar and bookmarks. In this
  case search engines will use it too.
* *Slug*, part of the page's URL; you'll usually want it to reflect the *Title*. In fact it will be
  generated automatically from the title, in an appropriate format - but it's always worth checking that your slugs are as short and sweet as
  possible.
* *Menu title* , to override what is displayed in navigation menus.
* *Page title*, usually used by django CMS templates for the ``<title>`` element of the page (which will otherwise simply use the *Title* field).
* *Description meta tag*, expected to be used to populate a ``<meta>`` tag in the document ``<head>``.

The next section will introduce django CMS's *structure mode*.

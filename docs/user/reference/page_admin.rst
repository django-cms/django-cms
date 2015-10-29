##########
Page admin
##########

*************
The interface
*************

.. _toolbar:

======================
The django CMS toolbar
======================

The toolbar is central to your content editing and management work in django
CMS.

.. figure:: /images/toolbar-site-menu.png

*django CMS*
============

Takes you back to home page of your site.

.. _site-menu:

*Site menu*
===========

*example.com* is the *Site menu* (and may have a different name for your site).
Several options in this menu open up administration controls in the side-frame:

* *Pages ...* takes you directly to the pages editing interface
* *Users ...* takes you directly to the users management panel
* *Administration ...* takes you to the site-wide administration panel
* *User settings ...* allows you to switch the language of the admin interface
  and toolbar
* *Disable toolbar* allows you to completely disable the toolbar and front-end
  editing, regardless of login and staff status. To reactivate them, you need
  to enter *edit mode* either manually or through the backend administration.

You can also *Logout* from this menu.

*Page menu*
===========

The *Page menu* contains options for managing the current page, and are either
self-explanatory or will be described in a forthcoming documentation section.

*History menu*
==============

Allows you to manage publishing and view publishing history of the current page.

*Language* menu
===============

*Language* allows you to switch to a different language version of the page
you're on, and manage the various translations.

Here you can:

* *Add* a missing translation
* *Delete* an existing translation
* *Copy* all plugins and their contents from an existing translation to the
  current one.

.. _structure-content-button:

The *Structure/Content* button
==============================

.. figure:: /images/structure-content.png
   :figwidth: 143
   :align: right

Allows you to switch between different editing modes (when you're looking at a
draft only).

.. _publishing-controller:

*Publishing controller*
=======================

The *Publishing controller* manages the publishing state of your page - options
are:

* **Publish page now** |publish-page-now| to publish an unpublished
* **Publish changes** |publish-changes| to publish changes made to an
  existing page
* **Edit** |edit| to open the page for editing
* **Save as draft** |save-as-draft| to update the page and exit editing mode
* **View published** does the same as "Save as draft"

.. |publish-page-now| image:: /images/publish-page-now.png
   :width: 119

.. |publish-changes| image:: /images/publish-changes.png
   :width: 107

.. |edit| image:: /images/edit.png
   :width: 45

.. |save-as-draft| image:: /images/save-as-draft.png
   :width: 101

The *disclosure triangle*
=========================

A toggle to hide and reveal the toolbar.

.. _side-frame:

==============
The side-frame
==============

.. figure:: /images/side-frame-controls.png
   :figwidth: 28
   :align: right

The *x* closes the side-frame. To reopen the side-frame, choose one of the
links from the *Site menu* (named *example.com* by default).

The triangle icon expands and collapses the side-frame, and the next expands
and collapses the main frame.

You can also adjust the side-frame's width by dragging it.

*******************
Admin views & forms
*******************

.. _page-list:

=========
Page list
=========

The *page list* gives you an overview of your pages and their status. By
default you get the basics:


.. figure:: /images/page-list-basic.png
   :figwidth: 300
   :align: right

The page you're currently on is highlighted in grey (in this case,
*Journalism*, the last in the list).

From left to right, items in the list have:

* an *expand/collapse* control, if the item has children (*Home* and *Cheese*
  above)
* *tab* that can be used to drag and drop the item to a new place in the list
* the page's *Title*
* a *soft-root* indicator (*Cheese* has *soft-root* applied; *Home* is the menu
  root anyway)
* *language version* indicators and controls:

  * *blank*: the translation does not exist; pressing the indicator will open
    its *Basic settings* (in all other cases, hovering will reveal
    *Publish*/*Unpublish* options)
  * *grey*: the translation exists but is unpublished
  * *green*: the translation is published
  * *blue (pulsing)*: the translation has an amended draft

If you expand the width of the side-frame, you'll see more:

.. figure:: /images/page-list-expanded.png
   :figwidth: 518

* *Menu* indicates whether the page will appear in navigation menus
* under *Actions*, options are:

  * *edit Basic settings*
  * *copy* page
  * *add child* (which can be placed before, after or below the page)
  * *cut* page
  * *delete* page

* *info* displays additional information about the page

.. _basic-page-settings:

===================
Basic page settings
===================

.. figure:: /images/page-basic-settings.png
   :figwidth: 300
   :align: right

To see a page's basic settings, select *Page settings...* from the *Page* menu.
If your side-frame is wide enough, you can also use the *page edit icon* that
appears in the *Actions* column in the page list view.

Required fields
===============

The page *Title* will typically be used by your site's templates, and displayed
at the top of the page and in the browser's title bar and bookmarks. In this
case search engines will use it too.

A *Slug* is part of the page's URL, and you'll usually want it to reflect the
*Title*. In fact it will be generated automatically from the title, in an
appropriate format - but it's always worth checking that your slugs are as
short and sweet as possible.

Optional fields
===============

*Menu title* is used to override what is displayed in navigation menus -
usually when the full *Title* is too long to be used there. For example, if the
*Title* is "ACME Incorporated: Our story", it's going to be far too long to
work well in the navigation menu, especially for your mobile users. "Our story"
would be a more appropriate *Menu title*.

*Page title* is expected to be used by django CMS templates for the `<title>`
element of the page (which will otherwise simply use the *Title* field). If
provided, it will be the *Page title* that appears in the browser's title bar
and bookmarks, and in search engine results.

*Description meta tag* is expected to be used to populate a `<meta>` tag in the document `<head>`.
This is not displayed on the page, but is used for example by search engines for indexing and to
show a summary of page content. It can also be used by other Django applications for similar
purposes. Description is restricted to 155 characters, the number of characters search engines
typically use to show content.

=================
Advanced settings
=================

A page's advanced settings are available by selecting *Advanced settings...*
from the *Page* menu, or from the **Advanced settings** button at the bottom of
the basic settings.

Most of the time it's not necessary to touch these settings.

.. figure:: /images/page-advanced-settings.png
   :figwidth: 300
   :align: right

* *Overwrite URL* allows you to change the URL from the default. By default,
  the URL for the page is the slug of the current page prefixed with slugs from
  parent pages. For example, the default URL for a page might be
  */about/acme-incorporated/our-vision/*. The *Overwrite URL* field allows you
  to shorten this to */our-vision/* while still keeping the page and its
  children organised under the *About* page in the navigation.
* *Redirect* allows you to redirect users to a different page. This is useful if
  you have moved content to another page but don't want to break URLs your users
  may have bookmarked or affect the rank of the page in search engine results.
* *Template* lets you set the template used by the current page. Your site will
  likely have a custom list of available templates. Templates are configured by
  developers to allow certain types of content to be entered into the page while
  still retaining a consistent layout.
* *Id* is an advanced field that should only be used in consultation with your
  site's developers. Changing this without consulting developers may result in
  a broken site.
* *Soft root* allows you to shorten the navigation hierarchy to something
  manageable on sites that have deeply nested pages. When selected, this page
  will act as the top-level page in the navigation.
* *Attached menu* allows you to add a custom menu to the page. This is
  typically used by developers to add custom menu logic to the current page.
  Changing this requires a server restart so should only be changed in
  consultation with developers.
* *Application* allows you to add custom applications (e.g. a weblog app) to the
  current page. This also is typically used by developers and requires a server
  restart to take effect.
* *X Frame Options* allows you to control whether the current page can be
  embedded in an iframe on another web page.

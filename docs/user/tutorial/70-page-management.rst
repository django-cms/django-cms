###############
Page management
###############

In this section you will learn how to:

* **rearrange pages** using the **page tree**
* manage the **page hierarchy**


Our menu of pages is growing:

.. image:: /user/tutorial/images/menu_multiple_items.png
   :alt: the navigation menu

As we continue adding pages, we're going to start running out of space in our navigation menu. There's room for three, but there won't be for 30.

We can see this list of pages in the admin too, by selecting *Pages* from the **site menu** in the toolbar:

.. image:: /user/tutorial/images/site-menu.png
   :alt: the site menu
   :align: center

This will show the **page list** in the overlay.

.. image:: /user/tutorial/images/page_tree_growing.png
   :alt: the page tree in the admin
   :align: center

The solution to the space problem is to *nest* pages, in a hierarchy, so that rather than::

    Home
    How to find us
    People

it becomes::

    Home
    Contact information
        How to find us
        People


***************************************
Create a new *Contact information* page
***************************************

So let's add a *Contact information* page and move the other two within it.

#.  Add a new page by selecting |add_page_from_tree|.

    .. |add_page_from_tree| image:: /user/tutorial/images/add_page_from_pagetree.png
       :alt: the 'Add page' button

#.  Give the new page a *Title*.

    .. image:: /user/tutorial/images/name_of_parent_page.png
       :alt: Enter title of parent page

#.  |save_button| the page.

    .. |save_button| image:: /user/tutorial/images/save_button.png
       :alt: Save


***********************
Rearrange the hierarchy
***********************

#.  Now move the *How to find us*, by dragging it over the *Contact
    information* page - you'll see a little "**+**" symbol light up when you're in the right place..

    .. image:: /user/tutorial/images/drag_drop_subpage.png
       :alt: Drag and drop subpage

#.  Do the same for the *People* page.

The page list should now look like this:

.. image:: /user/tutorial/images/page_tree_clean.png
   :alt: 'Page tree clean'
   :align: center


**************************************
Publish the *Contact information* page
**************************************

.. |publish-page-now| image:: /user/tutorial/images/publish-page-now.png
   :alt: 'Publish page now'

*Contact information* is a new page and hasn't yet been published.

You can see that in both its *language columns*, *en* and *de*, it has a grey dot, indicating that
it is not published in either of those languages.

You've previously :ref:`published pages <publishing_pages>` using the |publish-page-now| button,
but we'll show you a new way to do it:

#.  Find the *Contact information* page in the tree. Tap (if you're using a touch-screen) or hover
    over the publishing status indicator (|grey-dot|) in the *en* column next to its page name to
    reveal the options.

    .. |grey-dot| image:: /user/tutorial/images/grey-dot.png
       :alt: publishing status indicator icon
       :width: 38

#.  Select |publish| from the options.

    .. |publish| image:: /user/tutorial/images/publish.png
       :alt: Publish
       :width: 79

    .. image:: /user/tutorial/images/publish_page_from_page_tree.png
       :alt: Publish page from page tree
       :width: 400px

.. important::

    If you don't publish the parent page, *Contact information*, then none of its children will be
    accessible, even if they are themselves published.

And here's the result when you switch back to *Content* mode:

.. image:: /user/tutorial/images/contact_info_menu_extended.png
   :alt: Contact information extended menu
   :align: center

.. note::

    **How the menu works**

    In this menu, pages that have sub-pages are not themselves accessible. That is, you can't
    actually reach the *Contact information* page, and there's nothing on it anyway. It only exists
    in order to be a parent page for the two beneath it.

    This is a design choice made in this site's frontend layer. It's a common and popular choice,
    but you don't have to follow it - in fact in django CMS your menus can work almost any way you
    like.

    Implementing different menu systems is beyond the scope of this tutorial, but you will find
    more information in :ref:`customising_navigation_menus` and :ref:`how_menus_work`.


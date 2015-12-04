##############
Managing pages
##############

Our menu of pages is growing.

    .. image:: /user/tutorial/images/menu_multiple_items.png
       :alt: Menu multiple items
       :width: 340

We can see this list of pages in the admin too.


From the toolbar, choose *Pages* from the **site menu**.

    .. image:: /user/tutorial/images/site-menu.png
       :alt: the site menu
       :width: 435px

This will show the page list in the overlay.

    .. image:: /user/tutorial/images/page_tree_growing.png
       :alt: the page tree in the admin
       :width: 600

As we continue adding pages, we're going to start running out of space in our navigation menu at
the top of each page. There's room for three, but there won't be for 30.

The solution is to *nest* pages, in a hierarchy, so that rather than::

    Home
    How to find us
    People

it becomes::

    Home
    Contact information
        How to find us
        People

So let's add a *Contact information* page and move the other two within it.

#.  Add a new page by selecting |add_page_from_tree|.

    .. |add_page_from_tree| image:: /user/tutorial/images/add_page_from_pagetree.png
       :alt: the 'Add page' button

#.  Give the new page a *Title*.

    .. image:: /user/tutorial/images/name_of_parent_page.png
       :alt: Enter title of parent page
       :width: 100%

#.  |save_button| the page.

    .. |save_button| image:: /user/tutorial/images/save_button.png
       :alt: Save

#.  Now move the *How to find us* and *People* pages, by dragging them over the *Contact
    information* page - you'll see a little **+** symbol light up when you're in the right place..

    .. image:: /user/tutorial/images/drag_drop_subpage.png
       :alt: Drag and drop subpage
       :width: 400px

    The page list should now look like this:

    .. |page_tree_clean| image:: /user/tutorial/images/page_tree_clean.png
       :alt: 'Page tree clean'
       :width: 600

The page list should now look like this:

|page_tree_clean|

    .. |page_tree_clean| image:: /user/tutorial/images/page_tree_clean.png
       :alt: 'Page tree clean'
       :width: 600

Before you switch back to the *Content* mode, make sure the pages are published, otherwise you want be able to access them

To publish the page from the page tree, click on the gray dot next to the page name - in the corresponding language column - and select *publish*.

    .. image:: /user/tutorial/images/publish_page_from_page_tree.png
       :alt: Publish page from page tree
       :width: 400px

And here's the result when you switch back to *Content* mode:

    .. image:: /user/tutorial/images/contact_info_menu_extended.png
       :alt: Contact information extended menu
       :width: 400px

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


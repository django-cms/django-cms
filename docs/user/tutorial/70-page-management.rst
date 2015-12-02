##############
Managing pages
##############

Our menu of pages is growing.

|page_tree|
    .. |page_tree| image:: /user/tutorial/images/page_tree_growing.png
       :alt: 'Page tree'
       :width: 600

As we continue adding pages, we're going to start running out of space. There's room for three, but
there won't be for 30.

The solution is to *nest* pages, in a hierarchy, so that rather than::

    home
    how to find us
    people

it's::

    home
    contact information
        how to find us
        people

------------

|page_tree_clean|

    .. |page_tree_clean| image:: /user/tutorial/images/page_tree_clean.png
       :alt: 'Page tree clean'
       :width: 600


To do this, please follow these steps:

#. Add a new page by clicking on the **+ Add page** button. |add_page_from_tree|

    .. |add_page_from_tree| image:: /user/tutorial/images/add_page_from_pagetree.png
       :alt: 'Add Page from tree'
       :width: 100

#. Enter the title of the parent page.

    .. image:: /user/tutorial/images/name_of_parent_page.png
       :alt: Enter title of parent page
       :width: 100%

#. Hit **save** to create the page. |save_button|

    .. |save_button| image:: /user/tutorial/images/save_button.png
       :alt: 'Hit save button'
       :width: 60px

#. Now drag&drop the subpages below the new parent page and make sure you see the plus "+" symbol in front of the parent page.

    .. image:: /user/tutorial/images/drag_drop_subpage.png
       :alt: Drag and drop subpage
       :width: 400px


==============
The Page admin
==============

.. todo:: screenshots of following steps (if they are new steps)

.. todo:: write up steps properly

* select Explorer > Pages...
* show page list
* add another new page called "Contact information" and publish it
* move "how to find us" and "people" inside "Contact information"
* show result in navigation
* discuss how navigation works

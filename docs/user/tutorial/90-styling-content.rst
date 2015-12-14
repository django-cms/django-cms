####################################################
Styling content - introduction to responsive columns
####################################################

Our pages have some useful content, but they are not very well laid-out. For example, here's the
*How to find us* page:

.. image:: /user/tutorial/images/entire_contact_page.png
    :alt: Entire contact page

django CMS makes it easy possible to manage page layout as well as content. It doesn't really
matter whether you start by adding your content and then decide how to lay it out, or set up the
layout before you add the content.


******************************
The *Contact information* page
******************************

We'll start by doing something quite simple. We'll take the *Contact information* page, and use the
*columns* functionality to improve its layout by placing the text and the map side-by-side, in
columns.

**Don't worry** if you don't understand exactly what we're doing - all will be explained.

#.  Switch to structure mode using |structure-switch| and add a new *Row* plugin.

    .. |structure-switch| image:: /user/tutorial/images/structure-button.png
       :alt: the
       :width: 160

    .. image:: /user/tutorial/images/row_plugin.png
       :alt: Select Row plugin
       :align: center
       :width: 350

#.  When you create a *Row* plugin, it will ask about the columns you want it to contain - *how
    many* of them you want, and what their *widths* at different browser window sizes should be.

    .. image:: /user/tutorial/images/define_grid.png
       :alt: Define columns
       :align: right
       :width: 220

    *Create columns*
        2

    *col-xs*
        leave blank

    *col-sm*
        leave blank

    *col-md*
        12

    *col-lg*
        leave blank


#.  Expand the *Row* plugin to reveal the two *Column* plugins within it.

#.  Drag and drop the existing *Text* plugin *Bruno Bicycle Services...* into the first *Column*.

#.  Do the same for the *Google Map* plugin, dropping it into the second *Column*.

    .. image:: /user/tutorial/images/drag_content_to_column.png
       :alt: drag the original plugins into the new columns
       :align: center
       :width: 500

The final result in *Structure mode*:

.. image:: /user/tutorial/images/content_moved.png
   :alt: the final column plugin arrangement
   :align: center
   :width: 500

And in *Content mode*:

.. image:: /user/tutorial/images/row_result_contactpage.png
   :alt: the result in content mode
   :align: center

Here we have two columns - but try narrowing the browser window; when you get to a certain point, the layout will respond and display the two columns as rows instead:

.. image:: /user/tutorial/images/responsive.png
   :alt: the layout works on small and large displays
   :align: center


**************
How this works
**************

Bootstrap
=========

We're taking advantage of the `Bootstrap 3 <http://getbootstrap.com>`_ frontend framework that's
built into this site (through the `Aldryn Boilerplate Bootstrap 3
<http://aldryn-boilerplate-bootstrap3.readthedocs.org>`_), a complete and ready-to-use
implementation of various integrated frontend tools (see `What's inside
<http://aldryn-boilerplate-bootstrap3.readthedocs.org/en/latest/general/whatsinside.html>`_ for
more details).

Bootstrap 3 provides a responsive frontend - try resizing the browser window to see how your pages
respond - and is an excellent starting point for implementing web designs that don't re-invent the
wheel and can be guaranteed to work on a vast range of platforms and devices.

Bootstrap includes a row/column system. When we arrange columns within a row, as in the example
above, Bootstrap will display them in a row if the browser's of suitable width. If not, it will
collapse the row into fewer columns so that they do fit properly.

The `Aldryn Bootstrap 3 <https://github.com/aldryn/aldryn-bootstrap3/>`_ addons provides django CMS
plugins that can make use of the Bootstrap framework. It's designed to work with Aldryn Boilerplate
Bootstrap 3, but can be used independently of it, so you can use it with your own implementation of
the Bootstrap framework.

Bootstrap is not the only frontend framework of this sort, it's simply a popular one, and one that
several popular django CMS addons support out-of-the-box, and is also supported by a rich set of
plugins.


The column system and responsive layouts
========================================

.. note:: If this is already familiar to you, you can skip to :ref:`adding_four_columns` below.

Many such frameworks work in the same way: they're based on a column layout that's usually 12
units wide, and you can specify how many units each column occupies (including at different browser
window widths). It's beyond the scope of this document to explain how these systems work in detail,
but there are plenty of other useful resources.

In our tutorial site, we have adopted 24 rather than 12 column units for the page. So, a column of
12 units will be half a page wide, of 6 units a quarter of a page and so on::

    [----------24----------]
    [----12----][----12----]
    [---8--][---8--][---8--]
    [-4][-4][-4][-4][-4][-4]

And you can mix and match column widths, as long as each row contains 24 units::

    [----12----][--6-][3][3]
    [-4][-4][---8--][---8--]

Each column needs to be given a width in units (if no width is given, then the column will span the
entire available width of the row, but its behaviour may be unpredictable - similarly if you get
your addition wrong and the widths don't add up to 24!).

The problem is that a layout of columns (especially if you are dealing with more than two columns)
might look excellent on a wide display, but on a mobile phone, each one of those columns will be
uselessly narrow.

We can solve the problem by adopting *responsive* layouts.


Example: a two-column layout
-----------------------------

Here's the layout we created above for the *How to find us* page in a wider browser window::

    [----12----][----12----]

and in a narrower one::

    [----------24----------]
    [----------24----------]


Implementation
^^^^^^^^^^^^^^

*col-xs*
    the width value for *extra-small* displays (such as phones) - leave blank to imply ``24``

*col-sm*
    the width value for *small* displays (such as tablets) - leave blank to inherit from
    *col-xs*

*col-md*
    12

*col-lg*
    the width value for *large* displays (such as a wide desktop display) - leave blank to
    inherit from *col-md*


Example: a four-column layout
------------------------------

If we have a layout that is *four* columns wide in a window on a desktop display::

    [--6-][--6-][--6-][--6-]

then it can become *two rows of two columns* on a smaller display::

    [----12----][----12----]
    [----12----][----12----]

and *four rows of one column* on something like a mobile phone::

    [----------24----------]
    [----------24----------]
    [----------24----------]
    [----------24----------]


Implementation
^^^^^^^^^^^^^^

*col-xs*
    the width value for *extra-small* displays (such as phones) - leave blank to imply ``24``

*col-sm*
    12

*col-md*
    6

*col-lg*
    the width value for *large* displays (such as a wide desktop display) - leave blank to
    inherit from *col-md*

You can leave *col-xs* blank unless you want multiple columns even on mobile phone displays. In
most cases you won't. You also generally don't need to specify column arrangements for displays
larger than *col-md*, in which case you can leave *col-lg* blank too.

In practice, in most cases, specifying *col-sm* and - if you need it - *col-md* is enough.

We'll implement this layout in the next section.

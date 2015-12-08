###############
Styling content
###############

****************
The Contact page
****************

Our Contact page has some useful content, but it's not very well laid-out.

.. todo::

    image of Contact page with:

    * header created in 80-site-wide-content
    * content:

        Our workshop is at Zollstrasse 53, Zürich. We're open 24 hours a day, seven days a week,
        every day of the year.

        The map we added in 30-structure-content-modes

    * footer created in 80-site-wide-content

We'll use the *columns* functionality to place the text and the map side-by-side, in columns.

.. todo:: Please create screenshots of steps required to place the existing content into two columns

This is a very basic example of styling.


****************
The Home page
****************

Let's do something a bit more ambitious with the *Home* page of the site.

Here we have various items of content.

.. todo::

    show image of home page with:


    *   Some text from 20-create-page:

            We're proud to be the first and best 24-hour bicycle repair service in the city.

            Whatever your bicycle repair needs, you can rely on us to provide a top-quality service
            at very reasonable prices. We also operate a unique call-out service to come to the aid
            of stranded cyclists.

            No job's too small or too large, and we can repair anything from
            a puncture to a cracked frame.

    *   a news plugin from 50-news


.. _adding_four_columns:

*******************
Adding four columns
*******************

We're going to add four new points of information [example: https://www.dropbox.com/s/oisgwq6a9y485wd/Screenshot%202015-12-02%2008.33.23.png?dl=0.]

.. todo::

    illustrate the following steps. No need to show every single step, just
    the first time we do it (as indicated).

#.  As you have done previously, switch to *Edit* mode and then *Structure* mode.
#.  Add a *Row* plugin to the *Content* placeholder. [image]
#.  Add *Column* plugin to the *Row* plugin - that is, the *Column* is now inside the *Row*. [show plugin being added *inside* row; show settings] https://www.dropbox.com/s/qh1febdw37wz15t/Screenshot%202015-12-02%2008.35.26.png?dl=0
#.  Inside the *Column* plugin, add a *Text* plugin, containing: [show plugin being added *inside* column]

    *   Font awesome icon [show icon plugin]
    *   Set yourself free [large text]
    *   Never worry again about a bicycle malfunction - we're here for you
#.  **Save** [show completed plugin]
#.  Add 2nd Column plugin to the row just like the first one:
#.  Add a Text plugin, containing:

    *   Font awesome icon
    *   24 hour service [large text]
    *   Day or night, round the clock, when you break down, we'll be there
#.  **Save**
#.  Add 3rd Column plugin in just the same way, with:

    *   Workshop service [large text]
    *   Don't wait until you break down - keep your bike in top condition with a service

#.  And a 4th Column plugin:

    *   The Café [large text]
    *   Enjoy home-roasted coffee and home-made cakes in our cosy café next-door

.. todo:: show final result


**************
How this works
**************

Bootstrap
=========

We're taking advantage of the `Bootstrap 3 <http://getbootstrap.com>`_ frontend framework that's
built into this site (through the `Aldryn Boilerplate Bootstrap 3 addon
<http://aldryn-boilerplate-bootstrap3.readthedocs.org>`_).

It provides a responsive frontend - try resizing the browser window to see how your pages respond -
and is an excellent starting point for implementing web designs that don't re-invent the wheel and
can be guaranteed to work on a vast range of platforms and devices.

Bootstrap includes a row/column system. When we arrange columns within a row, as in the example
above, Bootstrap will display them in a row if the browser's of suitable width. If not, it will
collapse the row into fewer columns so that they do fit properly.

The `Aldryn Bootstrap 3 <https://github.com/aldryn/aldryn-bootstrap3/>`_ provides django CMS
plugins that can make use of the Bootstrap framework.

Bootstrap is not the only frontend framework of this sort, it's simply a popular one, and one that
several popular django CMS addons support out-of-the-box, and is also supported by a rich set of
plugins.


The column system and responsive layouts
========================================

.. note:: If this is already familiar to you, you can skip to :ref:`more_work_on_home_page` below.

Many such frameworks work in the same way: they're based on a column layout that's usually twelve
units wide, and you can specify how many units each column occupies (including at different browser
window widths). It's beyond the scope of this document to explain how these systems work in detail,
but there are plenty of other useful resources.

In our tutorial site, we have adopted 24 column units for the page. So, a column of 12 units will
be half a page wide, of 6 units a quarter of a page and so on::

    [----------24----------]
    [----12----][----12----]
    [---8--][---8--][---8--]
    [-4][-4][-4][-4][-4][-4]

And you can mix and match column widths, as long as each row contains 24 units::

    [----12----][--6-][3][3]
    [-4][-4][---8--][---8--]

Each column needs to be given a width in units (if no width is given, then the column will span the
entire available width of the row, but its behaviour may be unpredicatable - similarly if you get
your addition wrong and the widths don't add up to 24!).

The problem is that a layout of four or six or even eight columns might look excellent on a wide
display, but on a mobile phone, each one of those columns will be uselessly narrow.

We can solve the problem by adopting *responsive* layouts.

Our layout is four columns wide in a window on a desktop display::

    [--6-][--6-][--6-][--6-]

but becomes two rows of two columns on a smaller display::

    [----12----][----12----]
    [----12----][----12----]

and four rows of one column on something like a mobile phone::

    [----------24----------]
    [----------24----------]
    [----------24----------]
    [----------24----------]


Applying this to our column plugins
-----------------------------------

We can set this behaviour in the column plugin:

*col-xs*
    the width value for *extra-small* displays (such as phones) - leave blank to imply ``24``

*col-sm*
    the width value for *small* displays (such as tablets) - leave blank to inherit from ``col-xs``

*col-md*
    the width value for *medium* displays (such as a modest desktop display) - leave blank to
    inherit from *col-sm*

*col-lg*
     the width value for *large* displays (such as a wide desktop display) - leave blank to inherit
     from *col-md*

You can leave *col-xs* blank unless you want multiple columns even on mobile phone displays. In
most cases you won't. You also generally don't need to specify column arrangements for displays
larger than *col-md*, in which case you can leave *col-lg* blank too.

This means that in most cases, specifying *col-sm* and - if you need it - *col-md* is enough.

.. image:: /user/tutorial/images/column_settings.png
   :alt: the column width settings dialog
   :width: 120
   :align: right

If we set *col-sm* to ``12`` and *col-md* to ``6``, this means:

* on a mobile phone, display the items in this row in a single column
* on a typical tablet, display them in two rows of two columns
* on anything larger, display them in one row of four columns

... which is exactly :ref:`what we did above <adding_four_columns>`.


.. _more_work_on_home_page:

**************************
More work on the home page
**************************

To improve the home page further, let's put the original content into a row of two columns, with
the introductory text in the first column and the list of news items in the second.

This time, we'll arrange it thus for any browser window larger than that of a typical tablet::

    [--------18------][--6-]

... like this for a tablet::

    [----12----][----12----]

... and like this for a phone::

    [----------24----------]
    [----------24----------]

So the values you'll need to enter for the column plugins are:

first column:
    *col-xs*
        leave blank

    *col-sm*
        ``12``

    *col-md*
        ``18``

    *col-lg*
        leave blank

second column
    *col-xs*
        leave blank

    *col-sm*
        ``12``

    *col-md*
        ``6``

    *col-lg*
        leave blank

Let's create the necessary plugins.

#.  Create a new *Row* plugin.
#.  Inside it, create the first *Column* plugin (using the settings above).
#.  Add the second *Column* plugin and its settings.
#.  Drag and drop the *Text* plugin *We're proud to be...* into its new *Column*, and do the same
    for the *Map* plugin.

Now you can switch back to *Content* mode to admire your handiwork, and the way your home page
responds to different browser window widths.

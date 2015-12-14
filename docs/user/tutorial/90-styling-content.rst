###############
Styling content
###############

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

We'll start by improving the layout of the *Contact information* page, where we'll use the
*columns* functionality to place the text and the map side-by-side, in columns.

#.  Switch to structure mode using |structure-switch| and add a new *Row* plugin.

    .. |structure-switch| image:: /user/tutorial/images/structure-button.png
       :alt: the
       :width: 160

    .. image:: /user/tutorial/images/row_plugin.png
       :alt: Select Row plugin
       :align: center
       :width: 350

#.  When you create a *Row* plugin, it will ask about the columns you want it to contain - how
    many of them, and their widths at different browser window sizes.

    .. image:: /user/tutorial/images/define_grid.png
       :alt: Define columns
       :align: right
       :width: 170

    *Create columns*
        2

    *col-sm*
        24

    *col-md*
        12

    You can leave all the other values blank.

    If what this means isn't obvious to you, don't worry, we'll explain it all in a a moment.

#.  Expand the row to reveal the two columns.

#.  Drag and drop the *Text* plugin *Bruno Bicycle Services...* into its the first *Column*.

#.   Do the same for the *Google Map* plugin, dropping it into the second *Column*.

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
   :alt: Contact Page
   :align: center

Here we have two columns - but try narrowing the browser window; when you get to a certain point, the layout will respond and display the two columns as rows instead:

.. image:: /user/tutorial/images/responsive.png
   :alt: Responsive Webdesign
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
entire available width of the row, but its behaviour may be unpredicatable - similarly if you get
your addition wrong and the widths don't add up to 24!).

The problem is that a layout of columns (especially if you are dealing with more than two columns)
might look excellent on a wide display, but on a mobile phone, each one of those columns will be
uselessly narrow.

We can solve the problem by adopting *responsive* layouts.

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


Applying this to column plugins
-------------------------------

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

... which is exactly what we're going to do next for the home page.


.. _adding_four_columns:

************************************
Adding four columns to the home page
************************************

We're going to add four new points of information [example: https://www.dropbox.com/s/oisgwq6a9y485wd/Screenshot%202015-12-02%2008.33.23.png?dl=0.]

#.  As you have done previously, switch to *Edit* |edit-button| mode and then *Structure* |structure-button| mode.


.. |edit-button| image:: /user/tutorial/images/edit-button.png
   :alt: 'edit'
   :width: 45

.. |structure-button| image:: /user/tutorial/images/structure-button.png
   :alt: 'structure'
   :width: 148

#.  Add a *Row* plugin to the *Content* placeholder. Provide this *Row* plugin with settings as
    follows:

    .. image:: /user/tutorial/images/4_col_12_6.png
       :alt: Define columns
       :align: right
       :width: 180

    *Create columns*
        4

    *col-sm*
        12

    *col-md*
        6

    You can leave all the other values blank.

#.  Hit **Save** |save-button|

.. |save-button| image:: /user/tutorial/images/save_button.png
   :alt: 'save'
   :width: 60

#.  Inside the first *Column* plugin, add a new *Text* plugin, containing:

    .. image:: /user/tutorial/images/add_text_plugin.png
       :alt: Add text plugin
       :align: center
|

    *   Font awesome icon

    .. image:: /user/tutorial/images/fontawesome_icon.png
        :alt: Fontawesome Icon
        :width: 400
        :align: center
|

    *   Set yourself free [heading3]
    *   Never worry again about a bicycle malfunction - we're here for you
|

#.  Now, rather than go though the steps above three more times for the next three columns, let's
    save some effort by copy and pasting the *Text* plugin.

    #.  From the *plugin command menu* for the *Text* plugin, select *Copy*.

    .. image:: /user/tutorial/images/copy_plugin.png
        :alt: Copy plugin
        :align: center

    #.  Select the next (empty) *Column* plugin.
    #.  Select *Paste* from the menu.

    .. image:: /user/tutorial/images/paste_plugin.png
        :alt: Paste plugin
        :align: center


    You can then quickly change the text in the three copies:

    24 hour service
        Day or night, round the clock, when you break down, we'll be there

    Workshop service
        Don't wait until you break down - keep your bike in top condition with a service

    The Café
        Enjoy home-roasted coffee and home-made cakes in our cosy café next-door

.. image:: /user/tutorial/images/services_row_columns_example.png
    :alt: Services
    :align: center



*************************************
Further improvements to the home page
*************************************

Also on the home page, we have a *Text* plugin and a *Latest articles* plugin.

.. image:: /user/tutorial/images/styled_home_with_plugins.png
    :alt: Styled home with plugins
    :align: center

We don't need to repeat all the steps, but it's easy now to place these two plugins into separate *Column* plugins, just as you did for the content on the *How to find us* page.

This is how the content placeholder looks in the structure mode.

.. image:: /user/tutorial/images/styled_home_structure_mode.png
    :alt: Styled home structure mode
    :align: center

Seems like a lot, but it is actually pretty simple to achieve. Follow these steps:

1. Add a new row plugin with *2 columns* and set both to *col-sm-12*.

2. After they have been created, doubleclick on the first one and change the column width to *col-sm-16*. Open the second column and set that to *col-sm-8*.

3. Accordingly take the text plugin you firstly created on the homepage and drop it in the first column.

4. For the second column, chose the *image* plugin. Select a nice picute or upload one and hit *save*.

5. You might notice that that it does't align the top of the image to the text on the left. To make sure it looks nice, we're gonna add a new plugin to make some space.

    .. image:: /user/tutorial/images/bad_alignment.png
        :alt: Bad alignment and space
        :align: center

6. The spacer plugin helps to keep the white space between the elements and also to align them correctly. Just play around with the different options you have and select the one that fits the most.

    .. image:: /user/tutorial/images/spacer_plugin.png
        :alt: Spacer plugin
        :align: center

The same spacer plugin is used between the different sections.

|
|
*************************************
Adding a gallery plugin
*************************************

Next, we are going to add a gallery with the help of the boostrap *carousel* plugin.

1. As the carousel will be responsive, we will again make use of the grid plugin. This time we add a row and following columns::

    [-4-][--16--][-4-]

2. Accordingly we are going to use the bootstrap carousel plugin:

    .. image:: /user/tutorial/images/carousel_plugin.png
        :alt: Carousel plugin
        :align: center
        :width: 450

3. You can define a bunch of options for the carousel. Make sure you select the transition effect to create a smooth user experience


    .. image:: /user/tutorial/images/transition_effect.png
        :alt: Transition effect
        :align: center

4. Now we add the images by adding the *slide plugin* on the just created carousel plugin.

    .. image:: /user/tutorial/images/slide_plugin.png
        :alt: Slide plugin
        :align: center
        :width: 450

5. You will have to select an image from the filer plugin or upload a news one. Repeat this step for all slides you want to add.

6. Once you're done, dont' forget to publish your changes.

The result should look like this:

    .. image:: /user/tutorial/images/bootstrap_carousel.gif
        :alt: Bootstrap Carousel example
        :align: center



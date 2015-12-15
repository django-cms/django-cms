####################################################
Styling content - yet more work with columns
####################################################

In this section you will learn how to:

* create **asymmetric column layouts**
* use the **Spacer plugin** to create whitespace


***************************
Creating asymmetric columns
***************************

Also on the home page, we have a *Text* plugin and a *Latest articles* plugin. Let's add an image,
next to the *Text* plugin (i.e. in the same row).

You already know how to create a *Row* plugin, and how to add:

* existing plugins
* new plugins

to its *Columns* - so let's do that now:

#.  Create a new row, of two plugins. We'll want it to look like this on wider displays::

        [------16------][---8--]

    and like this on narrower ones::

        [----------24----------]
        [----------24----------]

    Setting the *col-sm* value for the columns to ``16`` (for the wider one) and ``8`` (for the
    narrower one) will achieve this.

    .. note::

        As the two values are different, you will need to apply them separately to each *Column*
        plugin - you can't just set them for all *Rows* as before.

#.  Drag and drop the existing *Text* plugin into the first *Column*.

#.  Add an *Image* plugin to the second *Column* (select one of the existing images in the Filer or
    upload your own, as before).

    .. image:: /user/tutorial/images/bad_alignment.png
        :alt: text and image in columns
        :align: center


***************************
Adding whitespace
***************************

In the example above, the alignment of the text and image is poor. We can fix that with
*Spacer* plugin, which simply adds whitespace.

There are also some other places where additional vertical space would be an improvement.

#.  Add a *Spacer* plugin above the *Image* plugin, in the same *Column*. Remember you can drag
    plugins to re-order them.

#.  Choose the appropriate size of spacer, and **Save**.

    .. image:: /user/tutorial/images/spacer_plugin.png
        :alt: Spacer plugin
        :align: center

#.  Add a *Spacer* between the *Text* plugin *What we offer* and the *Row* of four columns.

#.  Add a *Spacer* between the *Text* plugin *What we offer* and the *Row* of four columns.

#.  Add one after the four columns and the text that follows.

.. todo:: we need a new version of the image of the page.

.. image:: /user/tutorial/images/styled_home_with_plugins.png
    :alt: Styled home with plugins
    :align: center

.. image:: /user/tutorial/images/styled_home_structure_mode.png
    :alt: Styled home structure mode
    :align: right
    :width: 200

For your reference, here is the complete tree structure of the page (select it to see it at full
size).

Don't be overwhelmed by it; it's just a map, and you don't need to take it all in at once.

Once you become familiar with how they work, the django CMS page structure representations are
easy to understand and navigate.

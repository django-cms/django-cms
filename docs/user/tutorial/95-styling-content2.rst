####################################################
Styling content - more work with columns
####################################################

.. _adding_four_columns:

************************************
Adding four columns to the home page
************************************

We're going to add four things that we offer to our home page, like this, in just a few steps.

.. image:: /user/tutorial/images/services.png
    :alt: a list of four services
    :align: center


Creating the columns
====================

#.  As you have done previously, switch to |edit-button| mode and then, using |structure-button|,
    to *Structure* mode.

    .. |edit-button| image:: /user/tutorial/images/edit-button.png
       :alt: 'Edit'
       :width: 45

    .. |structure-button| image:: /user/tutorial/images/structure-button.png
       :alt: the 'Structure' toggle
       :width: 148

#.  Add a *Row* plugin to the *Content* placeholder. Provide this *Row* plugin with settings as
    follows:

    .. image:: /user/tutorial/images/4_col_12_6.png
       :alt: Define columns
       :align: right
       :width: 180

    *Create columns*
        4

    *col-xs*
        leave blank

    *col-sm*
        12

    *col-md*
        6

    *col-lg*
        leave blkank

    You can leave all the other values blank.

    If we set *col-sm* to ``12`` and *col-md* to ``6``, this means:

    * on a mobile phone, display the items in this row in a single column
    * on a typical tablet, display them in two rows of two columns
    * on anything larger, display them in one row of four columns

#.  Hit |save-button|.

    .. |save-button| image:: /user/tutorial/images/save_button.png
       :alt: 'Save'
       :width: 60


Creating the four items
=======================

#.  Select the  the first *Column* plugin, and add a new plugin:

    .. image:: /user/tutorial/images/add-plugin-to-column.png
       :alt: add a plugin inside the column
       :align: center

#.  Select *Text* from the list of available plugins:

    .. image:: /user/tutorial/images/add_text_plugin.png
       :alt: add text plugin
       :align: center

#.  In the text editor that opens, select the *CMS Plugins* menu, then choose *Icon*:

    .. image:: /user/tutorial/images/select-icon-plugin.png
       :alt: select icon plugin
       :align: center
       :width: 280

#.  Select the *Font Awesome* icon set, and find you want to use (note you can also search for
    icons by name):

    .. image:: /user/tutorial/images/fontawesome_icon.png
        :alt: Fontawesome Icon
        :width: 400
        :align: center

#.  **Show** the *Advanced* options of the *Icon* plugin dialog, and in *Classes* enter ``fa-4x``
    (this is a Font Awesome class, meaning "four times larger").

#.  **Save** the *Icon* plugin.

#.  Add some text below the icon, and apply some styling to it:

        Set yourself free

        Never worry again about a bicycle malfunction - we're here for you.


#.  Now, rather than go though the steps above three more times for the next three columns, let's
    save some effort by copy and pasting the *Text* plugin into each one.

    #.  From the *plugin command menu* for the *Text* plugin, select *Copy*.

    .. image:: /user/tutorial/images/copy_plugin.png
        :alt: Copy plugin
        :align: center

    Note that while the CMS is copying and pasting, a little cog icon (|cog-icon|) will rotate in
    the toolbar - the operation can take a few seconds.

    .. |cog-icon| image:: /user/tutorial/images/cog.png
        :alt: cog icon
        :width: 20

    #.  Select the next (empty) *Column* plugin.
    #.  Select *Paste* from the menu.

    .. image:: /user/tutorial/images/paste_plugin.png
        :alt: Paste plugin
        :align: center


    You can then quickly add an icon (search for *clock*, *wrench* and *coffee*), and change the
    text in the three copies:

    24 hour service
        Day or night, round the clock, when you break down, we'll be there

    Workshop service
        Don't wait until you break down - keep your bike in top condition with a service

    The Café
        Enjoy home-roasted coffee and home-made cakes in our cosy café next-door

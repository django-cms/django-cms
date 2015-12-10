###########################################################
Exploring other plugins - the Aldryn Bootstrap 3 collection
###########################################################

So far we have encountered and used a number of plugins; let's explore some more.


********
Carousel
********

You've already used nested plugins, when you worked with *Rows* and *Columns*. The *Carousel*
plugin works in a similar way: each *Carousel* contains a number of slides, that can contain images
(and optionally, text).

#.  Add a *Carousel* slide below the row of four icons you created in the :ref:`previous section
    <adding_four_columns>`.

#.  Add three *Carousel slide* plugins - they are the only kind you can add to a *Carousel* plugin -
    inside it. For each one, choose an image from the Filer :ref:`as you did previously
    <using_filer_files>`.

    .. todo:: an image of the completed carousel in structure mode

Usually, a plugin in *Content mode* looks much as it does when the page is published. However, some plugins, such as *Carousel*, show the content differently, so it's easier to edit. Hit **Publish changes** to see the final result.

.. todo:: an image of the completed carousel in live mode


****************
Accordion plugin
****************

The *Accordion* (an *Accordion* is a web widget that collapses and expands, hence the name, to
reveal its contents) plugin works in a similar way - you add the *Accordion* plugin to a
placeholder in the usual fashion, then add *Accordion item* plugins to the *Accordion*.

An *Accordion item* plugin itself contains other plugins; these are the items that can be shown and
hidden.

#.  Add an *Accordion* plugin to a placeholder on any page. Add a title to it, and **Save**.
#.  Add some *Accordion item* plugins to the *Accordion*.
#.  To each *Accordion item*, add another plugin - perhaps some *Text* or an *Image*.


******************
Link/Button plugin
******************

Another very useful plugin that you're likely to use a lot is *Link/Button*.

This plugin - like several others - can be used *inside a Text plugin*, not just in *Structure*
mode. We'll show this with another example:

#.  Go to the *How to find us* page.
#.  Open the *Text* plugin *Our workshop is at...*.
#.  Change this to read:

     Our workshop is at Zollstrasse 53, Zürich, right next to Zürich Hauptbahnhof.

     We’re open 24 hours a day, seven days a week, every day of the year.

    That's great, but let's change *Zürich Hauptbahnhof* into a link - so:

#.  In the text editor, select *Link/Button* from the *CMSPlugins* menu.

    .. todo:: add image

#.  Provide some details.

    .. tip::

        label
            Zürich Hauptbahnhof

        link
            https://en.wikipedia.org/wiki/Zürich_Hauptbahnhof

#.  Save the *Link/Button* plugin.

..  todo:: image of the link in the text

#.  Save the *Text* plugin.

The other options are self-explanatory, so feel free to experiment with them. Try turning the link
into a button, or add a link to another page within the site.

    .. todo:: add image of Accordion with one item expanded


************
More plugins
************

All the plugins above come from the `Aldryn Bootstrap 3 addon
<https://github.com/aldryn/aldryn-bootstrap3/wiki>`_. You've used several in the course of this
tutorial, but you'll find many others listed there too.

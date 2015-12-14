##################
Add a news section
##################

In this section we will add a News page and some news items to the site using, the *Aldryn News &
Blog* application.

Like Aldryn People, Aldryn News & Blog is a separate application that integrates seamlessly with
django CMS to provide new functionality for structured information. In this case the structured
information is news articles.


*********************
Create an **apphook**
*********************

Just as we did with Aldryn People, we should :ref:`create an apphook <create_an_apphook>` to create
a landing page for the news items.

We'll create a *News* page, and add an apphook for the Aldryn News & Blog application to it:

#.  Create and publish a new page called News.
#.  Open the page settings - *Page* > *Page settings* from the toolbar:

    .. image:: /user/tutorial/images/page-settings-button.png
        :alt: 'Page settings' can be found in the 'Page' menu
        :width: 170

#.  Select *Advanced Settings*:

    .. image:: /user/tutorial/images/advanced-settings-button.png
        :alt: the 'Advanced Settings' button
        :width: 170

#.  Find the *Application* field, which offers you a menu of options, and choose *Newsblog /
    Apphook_news*:

    .. image:: /user/tutorial/images/advanced-settings-choose-apphook.png
        :alt: select 'Newsblog / Apphook_news'

#.  **Save** your changes, and then **Publish** the page.

The page will now automatically display news items here - of course it's still empty at the moment, so let's continue by adding some news items.

    .. image:: /user/tutorial/images/automatic-news-list.png
        :alt: the empty news page


**********************
Creating news items
**********************

To create a new News item:

#.  Hit **Create**
#.  Select *New news/blog article*.
#.  Hit **Next**.
#.  Fill in the form to create the news item.

    .. tip::

        Name
            Our 1000th rescue mission

        Is published
            ✓

        Lead-in
            Last week our lauded cycle rescue service attended to its 1000th customer. On a stormy
            night Cyrus Henrik braved the elements once more, and out in the western suburbs he made
            short work of a snapped chain.

        Content
            It was all in a night's work for Cyrus, but for the stranded rider far from home in the
            cold and wet his swift arrival was warmly welcomed. Cyrus said: "It's been a pleasure
            to perform this service over the past two years, and I never expected it to become so
            popular. I hadn't even realised that this was going to be the 1000th call-out, but when
            I got back to the workshop all the team were waiting for me with champagne to
            celebrate." 1000 missions is quite a milestone; we look forward to the next 1000!

    .. image:: /user/tutorial/images/create-news-blog-article.png
        :alt: 'create new news/blog article modal'

#.  Hit **Create**.

Do the same for a second item:

.. tip::

    Name
        The Bruno Bicycle Services Café opens

    Is published
        ✓

    Lead-in
        If there's something cyclists can't do without, it's coffee and cake - so we have opened a
        brand new café serving home-roasted coffee and home-made cakes and light meals, right next
        door to the workshop on Zollstrasse.

    Content
        Last year we realised we'd spent a fortune ourselves at the local cafés and bakeries, so it
        was an obvious move: open our own café on the premises! Four months later, here it is, a
        cosy and warm place to sit and relax while your bike's being seen to at the end of long
        ride.

and a third:

.. tip::

    Name
        Repairing is caring

    Is published
        ✓

    Lead-in
        Every cyclist should own a basic toolkit to deal with possible breakdowns.

    Content
        Don't find yourself caught out by the small things. Pack a spare tube, a small pump, tyre
        levers and some patches, and you'll be equipped to deal with the major cause of cycling
        breakdowns - punctures.

The news articles will now be listed here, and this list will be always be kept up-to-date with a
selection of latest news items.

.. image:: /user/tutorial/images/three_articles.png
    :alt: the news page
    :width: 434
    :align: center

.. _use-news-plugin:


*****************
Use a news plugin
*****************

django CMS's plugin architecture means that we can re-use content very easily. For example, as well
as having our *News* page, we can show news items automatically, *in any page on the site*.

Typically, if your site has news, you will often choose to display some top news stories on the
home page too. So let's do that.

#.  Go back to the *Home* page.
#.  Switch to *Edit* mode, then *Structure* mode.
#.  Select **Add plugin** on the *Content* placeholder, just as you did when you :ref:`added a Map
    plugin <add_plugin>` to the *How to find us* page.
#.  Select the *News & Blog* > *Latest articles* plugin from the list that appears.
#.  You'll have to configure the plugin now; in the *App Config* field, select the Apphook you
    created earlier.
#.  **Save** the plugin.

.. image:: /user/tutorial/images/home_with_news_plugin.png
    :alt: the news plugin

##################
Add a news section
##################

In this section we will add a News page and some news items to the site using, the *Aldryn News &
Blog* application.

Like Aldryn People, Aldryn News & Blog is a separate application that integrates seamlessly with django CMS to provide new functionality for structured information. In this case the structured information is news articles.


*********************
Create an **apphook**
*********************

.. todo:: text needs updating

Just as we did with Aldryn People, we should create an apphook to create a landing page for the
news items.

We'll create a *News* page, and add an apphook for the Aldryn News & Blog application to it.

* create and publish a new page called News
* open page settings

    .. image:: /user/tutorial/images/page-settings-button.png
        :alt: 'page settings button'
        :width: 170

* go to advanced settings

    .. image:: /user/tutorial/images/advanced-settings-button.png
        :alt: 'page settings button'
        :width: 170

* from dropdown menu choose previously created apphook

    .. image:: /user/tutorial/images/advanced-settings-choose-apphook.png
        :alt: 'page settings button'

* publish page
* view page with automatic list of news in it

    .. image:: /user/tutorial/images/automatic-news-list.png
        :alt: 'page settings button'


**********************
Create some news items
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
        The City Bicycle Services Café opens

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


.. _use-news-plugin:

*****************
Use a news plugin
*****************

* go to home page
* switch to Edit mode
* enter Structure mode
* select **Add plugin** on *Content* placeholder
* select *Latest articles* plugin from list
* select the existing Apphook
* **Save**
* see news articles inserted into home page

    .. image:: /user/tutorial/images/home-page-news-articles.png
        :alt: 'page settings button'

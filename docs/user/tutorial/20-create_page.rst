#####################
Basic page operations
#####################

In this section you will learn how to:

* **create** and **publish** pages
* use **Edit mode** to modify existing content


.. _create-first-page:

*********************
Create the first page
*********************

Because this is a brand new site, when you visit it as a site administrator, django CMS's *Create
Page wizard* will open a new dialog box.

.. image:: /user/tutorial/images/welcome.png
   :alt: the 'Create Page' wizard
   :width: 400
   :align: center

#.  Select *Next*.
#.  Provide a *Title*.
#.  Add some basic text *Content*.
#.  Hit **Create**.

.. tip::

    You can provide any text and other content you like in this site, but if you'd like to use our
    examples, just copy them from these **Tip** boxes.

    Title
        Home

    Content
        We're proud to be the first and best 24-hour bicycle repair service in the city. Whatever
        your bicycle repair needs, you can rely on us to provide a top-quality service at very
        reasonable prices. We also operate a unique call-out service to come to the aid of stranded
        cyclists. No job's too small or too large, and we can repair anything from a puncture to a
        cracked frame.

.. image:: /user/tutorial/images/create_new_page.png
   :alt: Add Title and Content
   :width: 600
   :align: center


.. _publishing_pages:

**************
Publish a page
**************

.. |publish-page-now| image:: /user/tutorial/images/publish-page-now.png
   :alt: 'Publish page now'

Your newly-created page is just a *draft*, and won't actually be published until you decide to
publish it. As an editor, you can see drafts, but other visitors to your site can only see pages
that you have explicitly published.

* Hit |publish-page-now| to publish the page.

.. image:: /user/tutorial/images/new_home_page.png
   :alt: Newly-created page


*********************
Edit existing content
*********************

.. |edit| image:: /user/tutorial/images/edit-button.png
   :alt: 'Edit'

.. |view-published| image:: /user/tutorial/images/view-published.png
   :alt: 'View published'

.. note::

    At any time, you can make further changes to a page, by switching back into *Edit mode*, using
    the |edit| button that appears, and return to the *published* version of the page using the
    |view-published| button.

#.  Switch back into |edit| mode.

#.  Double-click (if you're using a pointer) or tap (if you're using a touch screen) on the
    paragraph of text to open it for editing.
#.  Make changes by breaking the text into paragraphs.
#.  **Save** it again.

.. note::

    The editor in this project is the *CKEditor*. It's powerful and has numerous features that will
    probably be fairly familiar. Feel free to explore, but don't worry, we'll come back to look at
    the more important ones soon.

You can continue making and previewing changes privately until you are ready to publish them.


**************
Add a new page
**************

Now we should create a second page, with contact information, so that customers can find our
workshop.

At the top of your page is the django CMS *toolbar*, with various useful tools in it.

.. image:: /user/tutorial/images/toolbar.png
   :alt: django-CMS toolbar

.. |create| image:: /user/tutorial/images/create.png
   :alt: 'Create'

#.  Hit |create| to create a second page. This opens the *Create page* wizard:

    .. image:: /user/tutorial/images/create-page-dialog.png
      :alt: the 'Create page' dialog

#.  Select **New Page**.
#.  Hit **Next**.
#.  Once again, give the page a *Title* and some basic text *Content*.

    .. tip::

        Title
            How to find us

        Content
            Our workshop is at Zollstrasse 53, Zürich. We're open 24 hours a day, seven days a week,
            every day of the year.

#.  Hit **Publish**.

#.  As before, go back into *Edit mode*, using the |edit| button, and double-click (or tap) on the
    *Our workshop...* text to edit it.

#.  Add a new paragraph, to serve as a heading: *Bruno Bicycle Services*.

#.  Apply a *Heading 2* (i.e. an HTML ``<h2>``) to the new paragraph, and **Save** the text once
    more.

    .. image:: /user/tutorial/images/apply-heading.png
       :alt: select Heading 3 from the Format menu
       :align: center

.. image:: /user/tutorial/images/how_to_find_us_page.png
   :alt: the 'How to find us' section


**********************
Some key Page settings
**********************

Open the page settings - *Page* > *Page settings* from the toolbar:

.. image:: /user/tutorial/images/page-settings-button.png
    :alt: 'Page settings' can be found in the 'Page' menu
    :width: 170

Slug
    The page's *slug* is used to form its URL. For example, a page *Lenses* that is a sub-page of
    *Photography* might have a URL that ends ``photography/lenses``. You can change the
    automatically-generated slug of a page if you wish to. Keep slugs short and meaningful, as they
    are useful to human beings and search engines alike. You can

Menu Title
    If you have a page called *Photography: theory and practice*, you might not want the whole
    title to appear in menus - shortening it to *Photography* would make more sense.

Page Title
    By default, a page's ``<title>`` element is taken from the *Title*, but you can override this
    here. The ``<title>`` element isn't displayed on the page, but is used by search engines and
    web browsers - as far as they are concerned, it's the page's real title.

Description meta tag
    A short piece of text that will be used by search engines (and displayed
    in lists of search results) and other indexing systems.

There are also some *Advanced Settings*, but you don't need to be concerned about these right now.


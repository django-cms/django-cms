:sequential_nav: both

.. _tutorial_first_page:

Your first page
===============

You will create a CMS page, drop a text plugin onto it, and publish it.
No code in this chapter — only the django CMS frontend editing interface.

Goal
----

At the end of this chapter, opening ``http://localhost:8000/about/`` in
a private browser window (logged out) shows a page with a heading and a
paragraph that you wrote.

1. Create a page
----------------

You should be logged in as the superuser created during install. The
django CMS toolbar is visible at the top of the screen.

#. In the toolbar, click **Create**. The wizard opens and asks what
   you want to create.

   .. image:: images/create_page_with_django_cms1.png
      :alt: the Create wizard with "New page" selected
      :align: center
      :width: 600

#. Choose **New page** and click **Next**. Set the title to ``About``
   and click **Create**.

   .. image:: images/create_page_with_django_cms2.png
      :alt: the New page form with a title typed in
      :align: center
      :width: 600

You are now on the new page in *edit mode*. The URL in your address bar
ends in ``/about/``.

2. Add some content
-------------------

The page is using the default template, which exposes a single
*placeholder* called ``Content`` in the middle of the page.

#. Click into the toggle on the top right of the page to open the structure board.
#. The structure board will show the page's single placeholder, called ``Content``. Click the
   the **plus button** next to it to add a plugin.

#. The plugin selector appears. Choose **Text**.
#. Type a heading and a short paragraph in the rich-text editor.
#. Click **Save** to commit changes to the page.

The page now shows your text.

.. note::

   **Screenshot suggested:** the empty ``Content`` placeholder in edit
   mode, with the *Add plugin* picker open and "Text" highlighted.

.. note::

   **Screenshot suggested:** the rich-text editor open over the page,
   showing a heading and a paragraph being typed.

3. Publish the page
-------------------

So far the page only exists in *draft*. Anonymous visitors cannot see
it.

#. In the toolbar, on the right side click **Publish **.
#. Open ``http://localhost:8000/about/`` in a private browser window or
   different browser where you are not logged in.

You should see your About page. If you see a 404 instead, you forgot
the publish step.

.. note::

   **Screenshot suggested:** side-by-side comparison of the page in edit
   mode (toolbar visible, dashed placeholder outline) and the same page
   viewed anonymously (no toolbar, clean rendering).

4. Create a second page and set it as the home page
---------------------------------------------------

Right now there is no homepage. Visiting ``http://localhost:8000/``
redirects to the only page that exists. Let us make that explicit.

#. In the toolbar, click **Create** → **New page**.
#. Title: ``Home``. Click **Create**.
#. In the toolbar's first menu (labelled "example.com") open **Pages...**.
#. The page tree opens. Click the **three dots** next to the Home new page and choose
   **Set as home**.
#. **Publish** the page (either through the toolbar as before, or by clicking on the circle
   next to the page in the page tree).

.. note::

   **Screenshot suggested:** the toolbar's *Page* menu open, showing the
   *Set as home* item.

Now ``http://localhost:8000/`` serves the *Home* page, and
``/about/`` continues to serve the About page.

What just happened
------------------

You created two CMS *pages*, each of which contained one
*placeholder*, each of which held one *plugin*. That is the core data
model of django CMS:

    **Page → placeholders → plugins**

You will see those three words in every later chapter.

For the conceptual story behind pages and placeholders, see
:doc:`/explanation/plugins` and :doc:`/explanation/publishing`. For the
toolbar's full menu structure, see :doc:`/reference/toolbar`.

Going further
-------------

- :doc:`/how_to/02-languages` — serve the same pages in multiple
  languages.
- :doc:`/how_to/05-caching` — page caching for production.

In the next chapter we will swap the default template for one of our
own and learn how placeholders are declared.

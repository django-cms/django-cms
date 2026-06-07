:sequential_nav: both

.. _tutorial_first_page:

Your first page
===============

You will create a CMS page, drop a text plugin onto it, and publish it.
No code in this chapter — only the django CMS frontend editing interface.

Goal
----

At the end of this chapter, opening ``http://localhost:8000/`` in a
private browser window (logged out) shows a *Home* page, and
``http://localhost:8000/about/`` shows a second *About* page — each with
a heading and a paragraph that you wrote.

1. Create your first page
-------------------------

You should be logged in as the superuser created during install. The
django CMS toolbar is visible at the top of the screen.

#. In the toolbar, click **Create**. The wizard opens and asks what
   you want to create.

   .. image:: images/create_page_with_django_cms1.png
      :alt: the Create wizard with "New page" selected
      :align: center
      :width: 600

#. Choose **New page** and click **Next**. Set the title to ``Home``.
   Leave the **Content** field empty — we will add the content from the
   structure board in the next step. Click **Create**.

   .. image:: images/create_page_with_django_cms2.png
      :alt: the New page form with a title typed in
      :align: center
      :width: 600

You are now on the new page in *edit mode*. The address bar shows an
internal editing URL (something like
``/admin/cms/placeholder/object/…/edit/…``) rather than the page's own
address — that is normal while you are editing.

.. note::

   The **first page you create automatically becomes the site's
   homepage**, so it is served at the site root
   (``http://localhost:8000/``) regardless of its slug. You can change
   which page is the homepage later from **Pages...** → the page's
   **three dots** → **Set as home**.

2. Add some content
-------------------

The page is using the default template, which exposes a single
*placeholder* called ``Page Content`` in the middle of the page.

#. Click the toggle on the top right of the page to open the structure
   board.
#. The structure board shows the page's single placeholder, called
   ``Page Content``. Click the **plus button** next to it to add a
   plugin.
#. The plugin selector appears. Choose **Text**.
#. Type a heading and a short paragraph in the rich-text editor.
#. Click **Save** to commit changes to the page.

The page now shows your text.

.. note::

   **Screenshot suggested:** the empty ``Page Content`` placeholder in
   edit mode, with the *Add plugin* picker open and "Text" highlighted.

.. note::

   **Screenshot suggested:** the rich-text editor open over the page,
   showing a heading and a paragraph being typed.

3. Publish the page
-------------------

So far the page only exists in *draft*. Anonymous visitors cannot see
it.

#. In the toolbar, on the right side click **Publish**.
#. Open ``http://localhost:8000/`` in a private browser window or a
   different browser where you are not logged in.

You should see your Home page. If you see a 404 instead, you forgot
the publish step.

.. note::

   **Screenshot suggested:** side-by-side comparison of the page in edit
   mode (toolbar visible, dashed placeholder outline) and the same page
   viewed anonymously (no toolbar, clean rendering).

4. Create a second page
-----------------------

Now add a second page that lives at its own URL.

#. In the toolbar, click **Create** → **New page**.
#. Set the title to ``About`` and leave the **Content** field empty.
   Click **Create**.
#. Add a **Text** plugin to its ``Page Content`` placeholder, just as
   you did for the home page, and write a heading and a paragraph.
#. **Publish** the page.

Because the homepage already exists, this second page is served at its
own slug. Open ``http://localhost:8000/about/`` in a private window —
you should see your About page.

.. note::

   **Screenshot suggested:** the page tree (**Pages...**) showing both
   *Home* (marked as the homepage) and *About*.

Now ``http://localhost:8000/`` serves the *Home* page, and
``/about/`` serves the About page.

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

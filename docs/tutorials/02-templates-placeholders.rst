:sequential_nav: both

.. _tutorial_templates:

Templates and placeholders
==========================

So far the CMS rendered your pages using the default template that ships
with the djangocms-frontend package. In this chapter you will write your own
template with two placeholders so editors can manage a header strip
*and* a body, and you will pick which template a page uses from the
toolbar.

Goal
----

At the end of this chapter, the homepage uses a template you wrote and
exposes two placeholders: ``Header`` and ``Body``. Editors can place
plugins into either one.

1. Create a templates directory
-------------------------------

In your project, create a ``templates/`` directory at the project root
if one does not already exist. Make sure Django is configured to find
it by setting, in ``settings.py``:

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [BASE_DIR / "templates"],
            "APP_DIRS": True,
            # ...
        },
    ]


2. Add a base template
----------------------

Create ``templates/base.html``:

.. code-block:: html+django

    {% load cms_tags sekizai_tags %}
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>{% page_attribute "page_title" %} – Coffee Roaster</title>
        {% render_block "css" %}
    </head>
    <body>
        {% cms_toolbar %}

        <header>
            {% placeholder "Header" %}
        </header>

        <main>
            {% placeholder "Body" %}
        </main>

        {% render_block "js" %}
    </body>
    </html>

A few things to notice:

- ``{% placeholder "Name" %}`` is what creates a placeholder. The name
  is what editors see in the toolbar.
- ``{% cms_toolbar %}`` is required for the toolbar to render — without
  it, you cannot edit.
- ``{% render_block "css" %}`` and ``{% render_block "js" %}`` come
  from `django-sekizai <https://django-sekizai.readthedocs.io>`_.
  Plugins ship their own CSS and JavaScript; when several plugins on
  the same page need the same asset, sekizai collects them so each
  block is rendered exactly once, in the right place in the document.
  Every django CMS template needs the ``"css"`` block in ``<head>``
  and the ``"js"`` block just before ``</body>``.

For everything ``{% placeholder %}`` accepts, see
:doc:`/reference/placeholders`. For the conceptual story, see
:doc:`/explanation/plugins`.

3. Register the template with the CMS
-------------------------------------

The CMS only offers templates it knows about. Tell it about
``base.html`` by adding to ``settings.py``:

.. code-block:: python

    CMS_TEMPLATES = [
        ("base.html", "Coffee Roaster — base"),
    ]

The second entry of each tuple is the human-readable label that appears
in the toolbar.

4. Switch the homepage to the new template
------------------------------------------

Restart ``runserver`` so the new setting is picked up, then in your
browser:

#. Open the *Home* page.
#. In the toolbar, open **Page** → **Templates** → choose
   *Coffee Roaster — base*.
#. The page reloads, now using your template.

You will see two empty placeholders labelled ``Header`` and ``Body``.

.. note::

   **Screenshot suggested:** the toolbar's *Page → Templates* submenu
   open, with *Coffee Roaster — base* in the list.

.. note::

   **Screenshot suggested:** the homepage in edit mode immediately after
   the template switch — two empty placeholders with the labels
   ``Header`` and ``Body`` visible above their outlines.

5. Fill the placeholders
------------------------

#. Drop a **Text** plugin into ``Header`` and type the site name —
   "Coffee Roaster".
#. Drop a **Text** plugin into ``Body`` and write a short welcome
   paragraph.
#. **Publish** the page.

Visit the homepage in a private window. You should see a header strip
above the body content, both editable.

.. note::

   **Screenshot suggested:** the final homepage with the site-name
   header strip on top and the welcome paragraph below.

What just happened
------------------

You now own the markup. Two new ideas appeared:

- A **template** declares which placeholders exist on a page. Different
  templates can declare different placeholders.
- **CMS_TEMPLATES** is the list of templates editors can pick from.

Anything you would do in a normal Django template — ``{% block %}``
inheritance, ``{% include %}``, ``{% url %}`` — works inside a CMS
template. The only CMS-specific tags you need for now are
``{% cms_toolbar %}`` and ``{% placeholder %}``.

A reusable region with ``static_alias``
---------------------------------------

If you want a region whose content is *the same on every page* (a
footer, for example), use ``{% static_alias %}`` instead of
``{% placeholder %}``. It works similar for editors, but the content
is stored once and reused everywhere:

.. code-block:: html+django

    <footer>
        {% static_alias "site_footer" %}
    </footer>

Add that to ``base.html`` if you like. The full mechanics live in
:doc:`/how_to/04-templates`.

Going further
-------------

- :doc:`/how_to/04-templates` — multiple templates, inheritance,
  per-page template overrides.
- :doc:`/how_to/01-placeholders` — placeholders outside CMS pages
  (e.g. on your own Django models).

In the next chapter we leave the toolbar and write our first custom
plugin in Python.

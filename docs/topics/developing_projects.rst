##############################################
Developing django CMS projects: best practices
##############################################

A django CMS project should be easy to maintain, and to integrate new applications into it.


========
Frontend
========


.. _best_practices_project_templates:

Templates
=========

A good django CMS project has a base template that can be inherited not only by multiple
:setting:`CMS_TEMPLATES`, but also by other applications that are part of the site.

We recommend an arrangement of three layers of inheritance; from the top down:

- *user-selectable page templates* as specified in :setting:`CMS_TEMPLATES`, which inherit from:
- ``base.html``, which inherits from:
- ``base_root.html``


``base_root.html``
------------------

``base_root.html`` sets up the components that will rarely if ever need to be changed, and that you
want to keep out of sight and out of mind as much as possible.

It should contains fundamental HTML elements (``<html>`` ``<body>`` and so on) so that these don't
need to be managed in inheriting templates.

It is also intended to be almost wholly content-agnostic - it doesn't know or care about how your
site's pages are going to be structured, and shouldn't need to. To this end it should provide an
empty ``{% block extend_root %}{% endblock %}``, that inheriting templates will override to provide
the page's content.

Furniture for site-wide JS and CSS components should also be in here.


``base.html``
-------------

``base.html`` is the template that *designers* will be most interested in. It fills in the bare
HTML elements of ``base_root.html``, and allows page content structures and layouts (headings,
``divs``, navigation menus and so on) to be created within ``{% block extend_root %}``.

``base.html`` should have contain an *empty* ``{% block content %}``, that - in templates that
extend it - is filled with ``{% placeholder content %}`` as well as width cues for images etc.


User-selectable page templates
------------------------------

Finally, users can select templates that inherit from ``base.html``. Even if your project has one
'standard' template and some minor variations, it is wise for *all* of them to inherit from a
``base.html``, so that they can all be edited independently. Even if your 'standard' template
changes nothing in ``base.html``, you should not be tempted to make ``base.html`` selectable by the
user.


Templates for errors
--------------------

- ``404.html`` for 404 error handling
- ``500.html`` for critical errors - **use only add generic without template tags**
- ``base.html`` as entry point for ``{% extends %}``

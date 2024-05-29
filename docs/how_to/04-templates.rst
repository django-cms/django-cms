##########################
How to work with templates
##########################

django CMS uses Django's template system to manage the layout of the CMS pages.

Django's Template System
========================

Django’s template language is designed to strike a balance between power and
ease. It’s designed to feel comfortable to those used to working with HTML.
If you have any exposure to other text-based template languages, such as Smarty
or Jinja2, you should feel right at home with Django’s templates.

The template system, out of the box, should be familiar to those who have
worked with desktop publishing or web design. Tags are surrounded by {% and %}
and denote the actions like loops and conditionals. Variables are surrounded by
{{ and }} and get replaced with values when the template is rendered.

Learn more about Django's template system in the
`Django documentation <https://docs.djangoproject.com/en/dev/topics/templates/>`_.


Django CMS and Django's Template System
=======================================

Django templates
----------------

You are totally free on how to name your templates, but we encourage you
to use the general Django conventions, including letting all templates inherit
from a base template by using the ``extends`` template tag or putting templates
in a folder named after the application providing it.

.. note::

   Some django CMS apps, like django CMS Alias, assume the base template is
   called ``base.html``. If you happen to prefer a different name for the base
   template and need to use such apps, you can create a ``base.html`` template
   that just consists of the ``{% extends "your_base_template.html" %}`` tag.

A fresh installation of django CMS using the quickstarter project or the
``djangocms`` command comes with a default template that for reasons of
convenience is provided by
`django CMS frontend <https://github.com/django-cms/djangocms-frontend>`_
and based on Bootstrap. We encourage you to create your own templates
as you would do for any Django project.

Generally speaking, django CMS is wholly frontend-agnostic. It doesn’t care
what your site’s frontend is built on or uses: You are free to decide which
CSS framework or JS library to use (if any).

When editing, the frontend editor will replace part of the current document's
DOM. This might require some JS widgets to be reinitialized.
See :ref:`frontend-integration` for more information.


CMS templates
-------------

You need to configure which templates django CMS should use. You can do this by
either setting the :setting:`CMS_TEMPLATES` or the :setting:`CMS_TEMPLATES_DIR`
settings.

You can select the template by page (and language) in the page menu of django
CMS' toolbar. By default, a page inherits its template from its parent page.
A root page uses the first template in :setting:`CMS_TEMPLATES` if no other
template is explicitly set.

To work seamlessly with django CMS, **your templates should include the**
``{% cms_toolbar %}`` **tag right as the first item in your template's**
``<body>``. This tag will render the toolbar for logged-in users.

.. note::

    The toolbar can also be displayed in views independent of django CMS.
    To provide a consistent user experience, many projects include the toolbar
    in their base template and share it with the whole Django project.


Also, you need to tell django CMS where to place the content of your pages. This
is done using **placeholders**. A placeholder is a named area in your template
where you can add content plugins. You can add as many placeholders as you want
to your templates.

To add a placeholder to your template, use the
``{% placeholder "name" %}`` template tag. The name is the name of the template
slot. It will be shown in the structure board of the frontend editor. Typical
names are "main", "sidebar", "footer", etc.

Finally, you need to add ``{% render_block "css" %}`` in the ``<head>`` section
of your CMS templates and ``{% render_block "js" %}`` right before the closing
``</body>`` tag of your CMS templates. This will render the CSS and JavaScript
at the appropriate places in your CMS templates.

django CMS uses `django-sekizai <https://github.com/django-cms/django-sekizai>`_
to manage CSS and JavaScript. To use the sekizai tags, you need to load the
``sekizai_tags`` template tags in your template: ``{% load sekizai_tags %}``.

Example
-------

Here is an example of a simple template that uses placeholders:

.. code-block:: html+django

    {% extends "base.html" %}
    {% load cms_tags djangocms_alias_tags %}
    {% block title %}{% page_attribute "page_title" %}{% endblock title %}
    {% block content %}
        <header>
            {% placeholder "header" %}
        </header>
        <main>
            {% placeholder "main" %}
        </main>
        <footer>
            {% static_alias "footer" %}
        </footer>
    {% endblock content %}

In this example, the template extends the base template, sets the title of the
page, and defines three placeholders: "header", "main", and "footer". The
placeholders are then rendered in the template.

The underlying base template could look like this:

.. code-block:: html+django

    {% load cms_tags sekizai_tags %}
    <!DOCTYPE html>
    <html>
        <head>
            <title>{% block title %}{% endblock title %}</title>
            {% render_block "css" %}
        </head>
        <body>
            {% cms_toolbar %}
            {% block content %}{% endblock content %}
            {% render_block "js" %}
        </body>
    </html>



Static aliases
==============

.. versionadded:: 4.0

.. note::

  Using ``static_alias`` requires the installation of
  `djangocms-alias <https://github.com/django-cms/djangocms-alias>`_ to work.

The package `djangocms-alias <https://github.com/django-cms/djangocms-alias>`_
provides an admin page in Django admin where special types of placeholders
called "static aliases" can be managed and its contents edited.

Frequent Use Cases:

1. Editors wish to manage repeated content centrally (DRY - don't repeat
   yourself)

2. Developers wish to add CMS functionality to their custom application's
   templates

**Repeated content**: Often, content areas such as a footer, a header or a
sidebar have identical content across all pages of a website.
`djangocms-alias <https://github.com/django-cms/djangocms-alias>`_ provides
a Django admin page for editors to manage such general site-wide content in
one place.

**Custom applications**: Templates in custom applications usually follow some
well-defined business logic which is normally hard-coded in the template.
However the same templates might include areas of "static" content, i.e.
content that editors wish to manage. As the django CMS :ttag:`placeholder` tag
only work in templates attached to the django CMS
:class:`~cms.models.pagemodel.Page` model,
`djangocms-alias <https://github.com/django-cms/djangocms-alias>`_
closes the gap by providing editors central access to such custom content areas.


.. _page_template:

CMS_TEMPLATE
============

``CMS_TEMPLATE`` is a context variable available in the context; it contains
the template path for CMS pages and application using apphooks, and the default
template (i.e.: the first template in :setting:`CMS_TEMPLATES`) for non-CMS
managed URLs.

This is mostly useful to use it in the ``extends`` template tag in the application
templates to get the current page template.

Example: cms template

.. code-block:: html+django

    {% load cms_tags sekizai_tags %}
    <html>
        <head>
            {% render_block "css" %}
        </head>
        <body>
        {% cms_toolbar %}
        {% block main %}
        {% placeholder "main" %}
        {% endblock main %}
        {% render_block "js" %}
        </body>
    </html>


Example: application template

.. code-block:: html+django

    {% extends CMS_TEMPLATE %}
    {% load cms_tags %}
    {% block main %}
    {% for item in object_list %}
        {{ item }}
    {% endfor %}
    {% static_placeholder "sidebar" %}
    {% endblock main %}

``CMS_TEMPLATE`` memorises the path of the cms template so the application
template can dynamically import it.

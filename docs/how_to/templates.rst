**********************
Working with templates
**********************

Application can reuse cms templates by mixing cms template tags and normal django
templating language.


static_placeholder
------------------

Plain :ttag:`placeholder` cannot be used in templates used by external applications,
use :ttag:`static_placeholder` instead.

.. _page_template:

CMS_TEMPLATE
------------
.. versionadded:: 3.0

``CMS_TEMPLATE`` is a context variable available in the context; it contains
the template path for CMS pages and application using apphooks, and the default
template (i.e.: the first template in :setting:`CMS_TEMPLATES`) for non-CMS
managed URLs.

This is mostly useful to use it in the ``extends`` template tag in the application
templates to get the current page template.

Example: cms template

.. code-block:: html+django

    {% load cms_tags %}
    <html>
        <body>
        {% cms_toolbar %}
        {% block main %}
        {% placeholder "main" %}
        {% endblock main %}
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


render_model
------------
.. versionadded:: 3.0

:ttag:`render_model` allows to edit the django models from the frontend by
reusing the django CMS frontend editor.
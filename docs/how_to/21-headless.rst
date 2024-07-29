########################################
 How to run django CMS in headless mode
########################################

.. versionadded:: 4.2

Django CMS is headless-ready. This means that you can use django CMS as a
backend service to provide content to the frontend technology of your choice.

Traditionally, django CMS serves the content as HTML pages. In headless mode,
django CMS does not publish the html page tree. To retrieve content in headless
mode you will need an application that serves the content from the CMS via an
API, such as djangocms-rest.

To run django CMS in headless mode, you simply remove the catch-all URL pattern
from your projects' ``urls.py`` file and replace it by an API endpoint:

.. code-block:: python

    urlpatterns = [
        path('admin/', admin.site.urls),
        # path('', include('cms.urls'))  # Remove this line
    ]

Now, django CMS will be fully accessible through the admin interface, but the
frontend will not be served. Once, you add an API endpoint, this will be the
only way to access the content.

.. note::

    You can also run a hybrid mode where you serve **both** the HTML pages
    and the content via an API, say, for an app. In this case, keep the django CMS' URLS and just add the
    API to your traditional project.


To add an API endpoint, you can use the ``djangocms-rest`` package, for example.
This package provides a REST API for django CMS. To install it, run:

.. code-block:: bash

    pip install djangocms-rest

Then, add the following to your ``urls.py`` file:

.. code-block:: python

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/', include('djangocms_rest.urls')),
    ]


.. note::

    Django CMS does not force you to use the ``djangocms-rest`` package. You can
    use any other package that provides an API for django CMS, with
    a different API such as GraphQL, for example.

    If you are using a different API package, you will need to follow the
    instructions provided by that package.


**************************
 Headless using templates
**************************

In traditional Django CMS, placeholders are defined in the templates and they
represent the regions where your plugins (the content) will be rendered. This
is easily done via using ``{% placeholder "placeholder_name" %}`` in your
Django templates.

If you keep the ``CMS_TEMPLATES`` setting in your project, you still will be
using templates to render the content when editing and previewing in headless
mode. In this case, the templates will be used to identify the placeholders of
a page.

This scenario requires templates to be present in the project for the benefit
of the editors only.


****************************
 Headless without templates
****************************

However, when running Django CMS headlessly without templates, you fully
decouple the front-end presentation layer (which includes templates) from the
CMS, and the configuration of placeholders must be handled differently.

First, set the :setting:`CMS_TEMPLATES` setting to an empty list in your
project's ``settings.py`` file (or remove it entirely):

.. code-block:: python

    CMS_TEMPLATES = []

Then, you can define the placeholders using the :setting:`CMS_PLACEHOLDERS`
setting:

.. code-block:: python

    CMS_PLACEHOLDERS = (
        ('single', ('content',), _('Single placeholder')),
        ('two_column', ('left', 'right'), _('Two columns')),
    )

The :setting:`CMS_PLACEHOLDERS` setting is a list of tuples. Each tuple
represents a placeholder configuration. Think of each placeholder configuration
replacing a template and providing the information on which placeholders
are available on a page: Like a template can have multiple ``{% placeholder %}``
template tags, a placeholder configuration can contain multiple placeholders.

The first element of the configuration tuple is the name of the placeholder
configuration. It is stored in a page's ``template`` field. It needs to be
unique. The second element is a tuple of placeholder slots available for the
configuration. The third element is the verbose description of the placeholder
configuration which will be shown in the toolbar. You can select a page's
placeholder configuration in the Page menu (instead of a template).

.. note::

    :setting:`CMS_PLACEHOLDERS` is only relevant, if no templates are used.
    If you define templates, placeholders are inferred from the templates.

    Also, do not confuse the :setting:`CMS_PLACEHOLDERS` setting with the
    :setting:`CMS_PLACEHOLDER_CONF` setting. The latter is used to configure
    individual placeholders, while the former is used to define available
    placeholders for a page.

This scenario is useful when you do not want to design templates and focus on
the content structure only. Editors will see a generic representation of the
plugins in a minimally styled template. Note that the ``css`` and ``js`` block
of the plugin templates will be loaded also in this case.

******************************
 Headless setup and app hooks
******************************

When running Django CMS in headless mode, you can still use app hooks to
integrate your Django apps with the CMS. App hooks allow you to attach Django
apps to a CMS page and render the app's content on that page. Those apps will
be served via django CMS' url patterns.

If the app provides API endpoints itself, they will need to be included
explicitly in the REST API. Please check the package you are using to create
the REST API on how to do this.

**************
 Hybrid setup
**************

You can also use django CMS in a hybrid setup, where you serve both the HTML
pages and the content via an API. In this case, you keep the django CMS' URLS
and just add the API to your traditional project.

Be careful, however, to have the API endpoints in your project's urls **before**
django CMS' catch-all HTML urls. Otherwise you run the risk of pages with
the wrong path shaddowing out the API endpoints.

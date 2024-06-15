########################################
 How to run django CMS in headless mode
########################################

.. versionadded:: 4.1

Django CMS is headless-ready. This means that you can use django CMS as a
backend service to provide content to the frontend technology of your choice.

Traditionally, django CMS serves the content as HTML pages. In headless mode,
django CMS does not publish the html page tree. To retrieve conten in headless
mode you will need an application that serves the content from the CMS via an
API, such as djangocms-rest. (You can also run a hybrid mode where you serve
**both** the HTML pages and the content via an API, say, for an app. In this
case, just add the API to your traditional project.)

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

To add an API endpoint, you can use the `djangocms-rest` package. This package
provides a REST API for django CMS. To install it, run:

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
    use any other package that provides an API for django CMS.

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
mode.

If ``CMS_TEMPLATES`` is set, the templates will be used to identify the
placeholders of a page.


****************************
 Headless without tempaltes
****************************

However, when running Django CMS headlessly, you can fully decouples the
front-end presentation layer (which includes templates) from the CMS, and the
configuration of placeholders is handled differently.

First, set the ``CMS_TEMPLATES`` setting to an empty list  in your project's
``settings.py`` file (or removing it entirely):

.. code-block:: python

    CMS_TEMPLATES = []

Then, you can define the placeholders using the ``CMS_PLACEHOLDERS`` setting:

.. code-block:: python

    CMS_PLACEHOLDERS = (
        ('single', ('content'), _('Single placeholder')),
        ('two_column', ('left', 'right'), _('Two columns')),
    )

The ``CMS_PLACEHOLDERS`` setting is a list of tuples. Each tuple represents a
placeholder configuration. The first element of the tuple is the name of the
placeholder configuration. The second element is a tuple of placeholder names.
The third element is the verbose description of the placeholder configuration
which will be shown in the user interface.

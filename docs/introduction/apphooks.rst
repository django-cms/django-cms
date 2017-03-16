.. _apphooks_introduction:

########
Apphooks
########

Right now, our Django Polls application is statically hooked into the project's
``urls.py``. This is all right, but we can do more, by attaching applications to
django CMS pages.


*****************
Create an apphook
*****************

We do this with an **apphook**, created using a :class:`CMSApp
<cms.app_base.CMSApp>` sub-class, which tells the CMS how to include that application.

Apphooks live in a file called ``cms_apps.py``, so create one in your Polls/CMS Integration
application, i.e. in ``polls_cms_integration``.

This is a very basic example of an apphook for a django CMS application:

.. code-block:: python

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _


    class PollsApphook(CMSApp):
        app_name = "polls"
        name = _("Polls Application")

        def get_urls(self, page=None, language=None, **kwargs):
            return ["polls.urls"]

    apphook_pool.register(PollsApphook)  # register the application


Instead of defining the URL patterns in another file ``polls/urls.py``, it also is possible
to return them directly, for instance as:

.. code-block:: python

    from django.conf.urls import url
    from polls.views import PollListView, PollDetailView

    class PollsApphook(CMSApp):
        # ...
        def get_urls(self, page=None, language=None, **kwargs):
            return [
                url(r'^$', PollListView.as_view()),
                url(r'^(?P<slug>[\w-]+)/?$', PollDetailView.as_view()),
            ]


What this all means
===================

In the ``PollsApphook`` class, we have done several key things:

* The ``app_name`` attribute gives the system a way to refer to the apphook - see :ref:`multi_apphook` for details
  on why this matters.
* ``name`` is a human-readable name for the admin user.
* The ``get_urls()`` method is what actually hooks the application in, returning a list of URL configurations that will
  be made active wherever the apphook is used.

**Restart the runserver**. This is necessary because we have created a new file containing Python
code that won't be loaded until the server restarts. You only have to do this the first time the
new file has been created.


.. _apply_apphook:

***************************
Apply the apphook to a page
***************************

Now we need to create a new page, and attach the Polls application to it through this apphook.

Create and save a new page, then publish it.

.. note:: Your apphook won't work until the page has been published.

In its *Advanced settings*, choose "Polls Application" from the *Application* menu, and save once
more.

.. image:: /introduction/images/select-application.png
   :alt: select the 'Polls' application
   :width: 400
   :align: center

Refresh the page, and you'll find that the Polls application is now available
directly from the new django CMS page.

You can now remove the mention of the Polls application (``url(r'^polls/', include('polls.urls',
namespace='polls'))``) from your project's ``urls.py`` - it's no longer even required there.

Later, we'll install a django-CMS-compatible :ref:`third-party application <third_party>`.

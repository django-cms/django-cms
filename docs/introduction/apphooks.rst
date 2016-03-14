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

Apphooks live in a file called ``cms_apps.py``, so create one in your Polls
application.

This is the most basic example of an apphook for a django CMS application:

.. code-block:: python

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _

    class PollsApphook(CMSApp):
        name = _("Polls Application")   # give your application a name (required)
        urls = ["polls.urls"]           # link your app to url configuration(s)
        app_name = "polls"


    apphook_pool.register(PollsApphook)  # register the application

Restart the runserver.


.. _apply_apphook:

***************************
Apply the apphook to a page
***************************

Now we need to create a new page, and attach the Polls application to it through this apphook.

Create and save a new page, then publish it.

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

Next, we're going to install a django-CMS-compatible third-party application.

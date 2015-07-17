########
Apphooks
########

Right now, our django Polls app is statically hooked into the project's
``urls.py``. This is all right, but we can do more, by attaching applications to
django CMS pages.

We do this with an **Apphook**, created using a :class:`CMSApp
<cms.app_base.CMSApp>` subclass, which tells the CMS how to include that app.

Apphooks live in a file called ``cms_apps.py``, so create one in your Poll
application.

This is the most basic example for a django CMS app:

.. code-block:: python

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _


    class PollsApp(CMSApp):
        name = _("Poll App")  # give your app a name, this is required
        urls = ["polls.urls"]  # link your app to url configuration(s)
        app_name = "polls"

    apphook_pool.register(PollsApp)  # register your app

You'll need to restart the runserver to allow the new apphook to become
available.

In the admin, create a new child page of the Home page. In its *Advanced
settings*, choose "Polls App" from the *Application* menu, and Save.

|apphooks|

.. |apphooks| image:: ../images/cmsapphook.png

Refresh the page, and you'll find that the Polls application is now available
directly from the new django CMS page. (Apphooks won't take effect until the
server has restarted, though this is not generally an issue on the runserver,
which can handle this automatically.)

You can now remove the inclusion of the polls urls in your project's
``urls.py`` - it's no longer required there.

Next, we're going to install a django-CMS-compatible third-party application.

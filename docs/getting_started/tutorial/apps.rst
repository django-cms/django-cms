CMS Apps
========

My First App (apphook)
~~~~~~~~~~~~~~~~~~~~~~

Right now, our django poll app is statically hooked into the project's
``urls.py``. This is not the preferred approach in django CMS. Ideally
you attach your apps to CMS pages.

For that purpose you write a CMS app. That is just a small class telling
the CMS how to include that app.

CMS apps live in a file called ``cms_app.py``, so go ahead and create
one in your poll's app folder.

This is the most basic example for a django CMS app.

.. code:: python

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _


    class PollsApp(CMSApp):
        name = _("Poll App")  # give your app a name, this is required
        urls = ["polls.urls"]  # link your app to url configuration(s)

    apphook_pool.register(PollsApp)  # register your app

You could now remove the inclusion of the polls urls in your project's
``urls.py``.

Run your server, add a new page for your app and edit it. Go to
‘Advanced Settings’ and choose ‘Polls App’ for ‘Application’. This will
hook your app into that very page. For these changes to take effect, you
will have to restart your server. If you reload your page now, you
should be presented with your poll app!

Let's get on by :doc:`blog`.

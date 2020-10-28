:sequential_nav: both

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


Create the apphook class
========================

Apphooks live in a file called ``cms_apps.py``, so create one in your Polls/CMS Integration
application, i.e. in ``polls_cms_integration``.

This is a very basic example of an apphook for a django CMS application:

.. code-block:: python

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool


    @apphook_pool.register  # register the application
    class PollsApphook(CMSApp):
        app_name = "polls"
        name = "Polls Application"

        def get_urls(self, page=None, language=None, **kwargs):
            return ["polls.urls"]


In this ``PollsApphook`` class, we have done several key things:

* ``app_name`` attribute gives the system a unique way to refer to the apphook. You can see from
  `Django Polls <https://github.com/divio/django-polls/blob/master/polls/urls.py#L6>`_ that the
  application namespace ``polls`` is hard-coded into the application, so this attribute **must**
  also be ``polls``.
* ``name`` is a human-readable name, and will be displayed to the admin user.
* ``get_urls()`` method is what actually hooks the application in, returning a
  list of URL configurations that will be made active wherever the apphook is used - in this case,
  it will use the ``urls.py`` from ``polls``.


Remove the old ``polls`` entry from the project's ``urls.py``
=============================================================

You must now remove the entry for the Polls application::

    re_path(r'^polls/', include('polls.urls', namespace='polls'))

from your project's ``urls.py``.

Not only is it not required there, because we reach the polls via the apphook
instead, but if you leave it there, it will conflict with the apphook's URL handling. You'll
receive a warning in the logs::

    URL namespace 'polls' isn't unique. You may not be able to reverse all URLs in this namespace.


Restart the runserver
=====================

**Restart the runserver**. This is necessary because we have created a new file containing Python
code that won't be loaded until the server restarts. You only have to do this the first time the
new file has been created.


.. _apply_apphook:

***************************
Apply the apphook to a page
***************************

Now we need to create a new page, and attach the Polls application to it through this apphook.

Create and save a new page, then publish it.

..  note:: Your apphook won't work until the page has been published.

In its *Advanced settings* (from the toolbar, select *Page > Advanced settings...*) choose "Polls
Application" from the *Application* pop-up menu, and save once more.

.. image:: /introduction/images/select-application.png
   :alt: select the 'Polls' application
   :width: 400
   :align: center

Refresh the page, and you'll find that the Polls application is now available
directly from the new django CMS page.

..  important::

    Don't add child pages to a page with an apphook.

    The apphook "swallows" all URLs below that of the page, handing them over to the attached
    application. If you have any child pages of the apphooked page, django CMS will not be
    able to serve them reliably.

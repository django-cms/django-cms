#####################
Extending the Toolbar
#####################

django CMS allows you to control what appears in the toolbar. This allows you
to integrate your application in the frontend editing mode of django CMS and
provide your users with a streamlined editing experience.


*************************
Registering toolbar items
*************************

There are two ways to control what gets shown in the toolbar.

One is the ``CMS_TOOLBARS`` setting. This gives you full control over which
classes are loaded, but requires that you specify them all manually.

The other is to provide ``cms_toolbars.py`` files in your apps, which will be
automatically loaded as long ``CMS_TOOLBARS`` is not set (or set to ``None``).
We'll work with this second method.


******************
Create the toolbar
******************

Create a new ``cms_toolbars.py`` file in your Polls application (note: *not* in
the Polls Plugin application):

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar
    from cms.utils.urlutils import admin_reverse
    from polls.models import Poll


    @toolbar_pool.register
    class PollToolbar(CMSToolbar):
        supported_apps = (
            'polls',
            'polls_plugin',
        )
        watch_models = [Poll,]

        def populate(self):
            if not self.is_current_app:
                return

            menu = self.toolbar.get_or_create_menu('poll-app', _('Polls'))

            menu.add_sideframe_item(
                name=_('Poll list'),
                url=admin_reverse('polls_poll_changelist'),
            )

            menu.add_modal_item(
                name=_('Add new poll'),
                url=admin_reverse('polls_poll_add'),
            )


What this all means
===================

What we're doing above is this:

* defining a ``CMSToolbar`` sub-class
* registering the toolbar class with ``@toolbar_pool.register``
* defining a ``populate()`` method that adds an item to the menu

The ``populate()`` method:

* checks whether we're in a page belonging to this application
* if so, it creates a menu if one's not already there
* adds a menu item to list all polls in the overlay
* adds a menu item to add a now poll as a modal window

Your ``cms_toolbars.py`` file should contain classes that extend ``cms.toolbar_base.CMSToolbar``
and are registered using ``cms.toolbar_pool.toolbar_pool.register()``. The register function can be
used as a decorator, as in the example above.

``CMSToolbar`` instances will have these attributes:

* ``toolbar``: the toolbar object
* ``request`` the current request
* ``is_current_app`` a flag indicating whether the current request is handled
  by the same app as the function is in (use ``supported_apps`` to add more
  apps that should be considered the "active app")
* ``app_path`` the name of the app used for the current request
* ``watch_models`` which allow the frontend editor to redirect the user to the model instance
  ``get_absolute_url`` whenever an instance is created or saved through the frontend editor
  (see :ref:`url_changes` for details)

``CMSToolbar`` sub-classes must implement a ``populate`` method. The ``populate``
method will only be called if the current user is a staff user.
``supported_apps`` is a list of app names that should be considered as
``is_current_app``. Usually you don't need to set ``supported_apps``, but in
our case we need it so ``is_current_app`` can be detected properly (because the
views for the poll app are in ``polls`` and our ``cms_toolbars.py`` is in the
``polls_plugin`` app).


**************
See it at work
**************

Visit your Polls page on your site, and you'll see a new *Polls* item in the toolbar.

There's a lot more to django CMS toolbar classes than this - see
:doc:`/how_to/toolbar` for more.

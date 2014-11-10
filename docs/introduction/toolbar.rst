#####################
Extending the Toolbar
#####################

django CMS allows you to control what appears in the toolbar. This allows you
to integrate your application in the frontend editing mode of django CMS and
provide your users with a streamlined editing experience.

Registering Toolbar items
#########################

There are two ways to control what gets shown in the toolbar.

One is the ``CMS_TOOLBARS`` setting. This gives you full control over which
classes are loaded, but requires that you specify them all manually.

The other is to provide ``cms_toolbar.py`` files in your apps, which will be
automatically loaded as long ``CMS_TOOLBARS`` is not set (or set to `None`).
We'll work with this second method.

Create a new ``cms_toolbar.py`` file in your Polls application (not: *not* in
the Polls Plugin application we were working with in the previous tutorial)::

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar


    @toolbar_pool.register
    class PollToolbar(CMSToolbar):
        def populate(self):
            if self.is_current_app:
                menu = self.toolbar.get_or_create_menu('poll-app', _('Polls'))
                url = reverse('admin:polls_poll_changelist')
                menu.add_sideframe_item(_('Poll overview'), url=url)

What we're doing above is this:

* defining a ``CMSToolbar`` subclass
* registering the toolbar class with ``@toolbar_pool.register``
* defining a ``populate()`` method that adds an item to the menu

The ``populate()`` method:

* checks whether we're in a page belonging to this application
* if so, it creates a menu item if one's not already there
* works out the URL for this menu item
* tells it that it should open in the admin sideframe



Your ``cms_toolbar.py`` file should contain classes that extend
``cms.toolbar_base.CMSToolbar`` and are registered using
``cms.toolbar_pool.toolbar_pool.register()``. The register function can be used
as a decorator.

A ``CMSToolbar`` subclass needs four attributes:

* ``toolbar``: the toolbar object
* ``request`` the current request
* `is_current_app` a flag indicating whether the current request is handled by the same app as the function is in
* `app_path` the name of the app used for the current request

``CMSToolbar`` subclasses must implement a ``populate`` method. The ``populate``
method will only be called if the current user is a staff user.

There's a lot more to django CMS toolbar classes than this - see
:doc:`/how_to/toolbar` for more.

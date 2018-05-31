.. _toolbar_introduction:

#####################
Extending the Toolbar
#####################

django CMS allows you to control what appears in the toolbar. This allows you
to integrate your application in the frontend editing mode of django CMS and
provide your users with a streamlined editing experience.


******************
Create the toolbar
******************

We'll create a toolbar using a ``cms.toolbar_base.CMSToolbar`` sub-class.

Create a new ``cms_toolbars.py`` file in your Polls/CMS Integration application. Here's a basic example:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar
    from cms.utils.urlutils import admin_reverse
    from polls.models import Poll


    class PollToolbar(CMSToolbar):
        supported_apps = (
            'polls',
            'polls_cms_integration',
        )

        watch_models = [Poll]

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


    toolbar_pool.register(PollToolbar)  # register the toolbar


.. note:: Don't forget to restart the runserver to have your new toolbar item recognised.


What this all means
===================

* ``supported_apps`` is a list of application names in which the toolbar should be active. Usually you don't need to set
  ``supported_apps`` - the appropriate application will be detected automatically. In this case (since the views for
  the Polls application are in ``polls``, while our ``cms_toolbars.py`` is in the ``polls_cms_integration``
  application) we need to specify both explicitly.
* ``watch_models`` allows the frontend editor to redirect the user to the model instance
  ``get_absolute_url`` whenever an instance of this model is created or saved through the frontend editor
  (see :ref:`url_changes` for details).
* The ``populate()`` method, which populates the toolbar menu with nodes, will only be called if the current user is a
  staff user. In this case it:

  * checks whether we're in a page belonging to this application, using ``self.is_current_app``
  * ... if so, it creates a menu, if one's not already there (``self.toolbar.get_or_create_menu()``)
  * adds a menu item to list all polls in the overlay (``add_sideframe_item()``)
  * adds a menu item to add a new poll as a modal window (``add_modal_item()``)


**************
See it at work
**************

Visit your Polls page on your site, and you'll see a new *Polls* item in the toolbar.

It gives you quick access to the list of Polls in the Admin, and gives you a shortcut for
creating a new Poll.

There's a lot more to django CMS toolbar classes than this - see
:ref:`toolbar_how_to` for more.

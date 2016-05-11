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
We'll work with this second method, and build up the functionality step-by-step.


***********************
Create the toolbar menu
***********************

We create the menu using a :class:`CMSApp
<cms.toolbar_base.CMSToolbar>` sub-class, and populate it in the ``populate()`` method.

Create a new ``cms_toolbars.py`` file in your Polls/CMS Integration application:

.. code-block:: python

    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar
    from cms.utils.urlutils import admin_reverse


    class PollToolbar(CMSToolbar):

        def populate(self):

            # create the menu
            menu = self.toolbar.get_or_create_menu(
                'polls-application',        # give your menu an internal identifier
                _('Polls')                  # provide a name for the menu
            )

    toolbar_pool.register(PollToolbar)

.. note:: Don't forget to restart the runserver to have your new toolbar item recognised.

If you refresh a page on your site, you'll see the new *Polls* menu. It's empty however - now we need to add something
to it.


Add menu items
==============

Let's add two items, commands for:

* a list of Polls, that will appear in the sideframe
* a new Poll

We need to edit the ``populate()`` method, as follows:


.. code-block:: python
   :emphasize-lines: 9-12, 14-17

    def populate(self):

        # create the menu
        menu = self.toolbar.get_or_create_menu(
            'polls-application',        # give your menu an internal identifier
            _('Polls')                  # provide a name for the menu
        )

        menu.add_sideframe_item(
            name=_('Poll list'),
            url=admin_reverse('polls_poll_changelist'),
        )

        menu.add_modal_item(
            name=_('Add new poll'),
            url=admin_reverse('polls_poll_add'),
        )

In each case, the method specifies how we're going to display the resource that opens next (``add_sideframe_item()`` or
``add_modal_item()``). We also provide the ``name``, and the admin ``url`` that we want to make use of. The URL is
actually derived automatically by Django, from the Polls' application admin views.

Refresh the page, and explore the new menu items you have created.

Control when the menu appears
=============================


At the moment, the menu appears whatever page we're looking at - but perhaps it would make more sense to have it
displayed only when we're actually looking on a page that is related to Polls.

So, in the ``populate()`` method we should check whether the current request is being handled by this application, using the ``is_current_app`` attribute of ``CMSToolbar`` (and exit without doing anything if not).

There's one complication: the application that would qualify as ``is_current_app`` - Polls/CMS Integration - *isn't*
the same application that handles the request - Polls. So, we will also need to inform the ``PollToolbar`` that
Polls *also* counts as "this application", by explicitly providing a ``supported_apps`` attribute.

That will look like this:

.. code-block:: python
   :emphasize-lines: 2-4, 6-8

    class PollToolbar(CMSToolbar):
        supported_apps = (
            'polls',
        )

        def populate(self):
            if not self.is_current_app:
                return

            # create the menu
            menu = self.toolbar.get_or_create_menu(
                'polls-application',        # give your menu an internal identifier
                _('Polls')                  # provide a name for the menu
            )

            [...]

And now, the menu for Polls will only appear on the pages where it should.


************
There's more
************

There is quite a bit more we can do with menus. For example, you could check whether:

* we're looking at a Poll instance
* we have admin permissions to edit Polls

and on that basis, add a menu item to *Edit this Poll*. However, that's beyond the scope of this basic introduction, but you'll find more guidance and examples in :ref:`toolbar_how_to`.

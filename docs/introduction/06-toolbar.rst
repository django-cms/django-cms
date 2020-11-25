:sequential_nav: both

.. _toolbar_introduction:

#####################
Extending the toolbar
#####################

django CMS allows you to control what appears in the toolbar. This allows you
to integrate your application in the frontend editing mode of django CMS and
provide your users with a streamlined editing experience.

In this section of the tutorial, we will add a new *Polls* menu to the toolbar.


*********************************
Add a basic ``PollToolbar`` class
*********************************

We'll add various controls to the toolbar, using a ``cms.toolbar_base.CMSToolbar`` sub-class.


Add a menu to the toolbar
=========================

Start by adding a new file, ``cms_toolbars.py``, to your Polls/CMS Integration application, and
create the ``CMSToolbar`` class:

..  code-block:: python

    from cms.toolbar_base import CMSToolbar
    from cms.toolbar_pool import toolbar_pool
    from polls.models import Poll


    class PollToolbar(CMSToolbar):

        def populate(self):
            self.toolbar.get_or_create_menu(
                'polls_cms_integration-polls',  # a unique key for this menu
                'Polls',                        # the text that should appear in the menu
                )


    # register the toolbar
    toolbar_pool.register(PollToolbar)


..  note::

    Don't forget to restart the runserver to have your new ``cms_toolbars.py`` file recognised.

You will now find, in every page of the site, a new item in the toolbar:

.. image:: /introduction/images/toolbar-polls.png
   :alt: The Polls menu in the toolbars
   :width: 630

The ``populate()`` method is what gets called when the toolbar is built. In it, we're using
:meth:`get_or_create_menu() <cms.toolbar.toolbar.CMSToolbar.get_or_create_menu()>` to add a *Polls*
item to the toolbar.


.. _add-nodes-to-polls-menu:

Add nodes to the *Polls* menu
-----------------------------

So far, the *Polls* menu is empty. We can extend ``populate()`` to add some items.
``get_or_create_menu`` returns a menu that we can manipulate, so let's change the ``populate()``
method to add an item that allows us to see the full list of polls in the sideframe, with
:meth:`add_sideframe_item() <cms.toolbar.items.ToolbarAPIMixin.add_sideframe_item()>`.

..  code-block:: python
    :emphasize-lines: 1, 8, 10-13

    from cms.utils.urlutils import admin_reverse
    [...]


    class PollToolbar(CMSToolbar):

        def populate(self):
            menu = self.toolbar.get_or_create_menu('polls_cms_integration-polls', 'Polls')

            menu.add_sideframe_item(
                name='Poll list',                              # name of the new menu item
                url=admin_reverse('polls_poll_changelist'),    # the URL it should open with
            )

After refreshing the page to load the changes, you can now see the list of polls directly from
the menu.

Also useful would be an option to create new polls. We'll use a modal window for this, invoked with
:meth:`add_modal_item() <cms.toolbar.items.ToolbarAPIMixin.add_modal_item()>`. Add the new code to the
end of the ``populate()`` method:

..  code-block:: python
    :emphasize-lines: 6-9

    class PollToolbar(CMSToolbar):

        def populate(self):
            [...]

            menu.add_modal_item(
                name='Add a new poll',                # name of the new menu item
                url=admin_reverse('polls_poll_add'),  # the URL it should open with
            )


Add buttons to the toolbar
==========================

As well as menus, you can add buttons to the toolbar in a very similar way. Rewrite the
``populate()`` method, noting how closely the structure of this code matches that for adding menus.

..  code-block:: python
    :emphasize-lines: 3-13

    def populate(self):

        buttonlist = self.toolbar.add_button_list()

        buttonlist.add_sideframe_button(
            name='Poll list',
            url=admin_reverse('polls_poll_changelist'),
        )

        buttonlist.add_modal_button(
            name='Add a new poll',
            url=admin_reverse('polls_poll_add'),
        )


*******************
Further refinements
*******************

The buttons and menu for Polls appear in the toolbar everywhere in the site. It would be useful to
restrict this to pages that are actually relevant.

The first thing to add is a test right at the start of the ``populate()`` method:

..  code-block:: python
    :emphasize-lines: 3-4

        def populate(self):

            if not self.is_current_app:
                return

            [...]

The ``is_current_app`` flag tells us if the function handling this view (e.g. the list of polls)
belongs to the same application as the one responsible for this toolbar menu.

Often, this can be detected automatically, but in this case, the view belongs to the ``polls``
application, whereas the toolbar menu belongs to ``polls_cms_integration``. So, we need to tell the
``PollToolbar`` class explicitly that it's actually associated with the ``polls`` application:

..  code-block:: python
    :emphasize-lines: 3

    class PollToolbar(CMSToolbar):

        supported_apps = ['polls']

Now, the buttons/menu will only appear in relevant pages.


********************************
The complete ``cms_toolbars.py``
********************************

For completeness, here is the full example:

..  code-block:: python

    from cms.utils.urlutils import admin_reverse
    from cms.toolbar_base import CMSToolbar
    from cms.toolbar_pool import toolbar_pool
    from polls.models import Poll


    class PollToolbar(CMSToolbar):
        supported_apps = ['polls']

        def populate(self):

            if not self.is_current_app:
                return

            menu = self.toolbar.get_or_create_menu('polls_cms_integration-polls', 'Polls')

            menu.add_sideframe_item(
                name='Poll list',
                url=admin_reverse('polls_poll_changelist'),
            )

            menu.add_modal_item(
                name=('Add a new poll'),
                url=admin_reverse('polls_poll_add'),
            )

            buttonlist = self.toolbar.add_button_list()

            buttonlist.add_sideframe_button(
                name='Poll list',
                url=admin_reverse('polls_poll_changelist'),
            )

            buttonlist.add_modal_button(
                name='Add a new poll',
                url=admin_reverse('polls_poll_add'),
            )

    toolbar_pool.register(PollToolbar)  # register the toolbar

This is just a basic example, and there's a lot more to django CMS toolbar classes than this - see
:ref:`toolbar_how_to` for more.

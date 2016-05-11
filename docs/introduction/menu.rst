#############################
Extending the navigation menu
#############################

You may have noticed that while our Polls application has been integrated into
the CMS, with plugins, toolbar menu items and so on, the site's navigation menu
is still only determined by django CMS Pages.

We can hook into the django CMS menu system to add our own nodes to that
navigation menu.

***********************
Create the toolbar menu
***********************

We create the menu using a :class:`CMSAttachMenu <cms.menu_bases.CMSAttachMenu>` sub-class, and use the ``get_nodes()``
method to add the nodes.

For this we need a file called ``cms_menus.py`` in our application. Add ``cms_menus.py`` in ``polls_cms_integration/``:

.. code-block:: python

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _

    from cms.menu_bases import CMSAttachMenu
    from menus.base import NavigationNode
    from menus.menu_pool import menu_pool

    from polls.models import Poll


    class PollsMenu(CMSAttachMenu):
        name = _("Polls Menu")  # give the menu a name this is required.

        def get_nodes(self, request):
            nodes = []

            # loop over all the Poll objects in the database
            for poll in Poll.objects.all():

                # create a NavigationNode based on each one
                node = NavigationNode(
                    title=poll.question,
                    url=reverse('polls:detail', args=(poll.pk,)),
                    id=poll.pk,
                )
                nodes.append(node)
            return nodes

    menu_pool.register_menu(PollsMenu)


What's happening here:

* we define a ``PollsMenu`` class, and register it
* we give the class a ``name`` attribute (will be displayed in admin)
* in its ``get_nodes()`` method, we build and return a list of nodes, where:
* first we get all the ``Poll`` objects
* ... and then create a ``NavigationNode`` object from each one
* ... and return a list of these ``NavigationNodes``


************************
Apply the menu to a page
************************

This menu class is not active until attached to a page.

In the *Polls* page's *Advanced settings*, choose "Polls Menu" in the *Attached menu* field and save.

You'll now see that every Poll is represented as a node in a sub-menu for the Polls page.

.. image:: /introduction/images/select-menu.png
   :alt: select 'Polls Menu'
   :align: center


Apply it automatically
======================

Note that you could have added the menu to any page. However, we can also attach a menu like this not just to a *page*,
but to an *apphook* - so that whatever page an application is attached to, the menu will be attached to.

We'll do this in the ``cms_apps.py``, where the apphook class ``PollsApphook`` lives - the amended lines are highlighted:

.. code-block:: python
   :emphasize-lines: 4, 10

    from django.utils.translation import ugettext_lazy as _
    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from polls_cms_integration.cms_menus import PollsMenu

    class PollsApphook(CMSApp):
        name = _("Polls Application")   # give your application a name
        urls = ["polls.urls"]           # link it to URL configuration(s)
        app_name = "polls"              # set the default application namespace
        menus = [PollsMenu]             # set a menu for this apphook

Any page that is attached to the ``Polls`` application will now have sub-menu items for each of the Polls in the
database. It doesn't stop you from *also* adding menus to pages manually, but guarantees that they will appear on the
Polls page at least.

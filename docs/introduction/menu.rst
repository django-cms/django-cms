#############################
Extending the navigation menu
#############################

You may have noticed that while our Polls application has been integrated into
the CMS, with plugins, toolbar menu items and so on, the site's navigation menu
is still only determined by django CMS Pages.

We can hook into the django CMS menu system to add our own nodes to that
navigation menu.

For this we need a file called ``cms_menus.py`` in our application. Add
``polls_plugin/cms_menus.py``:

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
            """
            This method is used to build the menu tree.
            """
            nodes = []
            for poll in Poll.objects.all():
                node = NavigationNode(
                    title=poll.question,
                    url=reverse('polls:detail', args=(poll.pk,)),
                    id=poll.pk,  # unique id for this node within the menu
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

This menu class is not active until attached to the apphook we created earlier.
So open your ``cms_apps.py`` and add::

    from polls_plugin.cms_menus import PollsMenu

for importing ``PollsMenu`` and::

    menus = [PollsMenu]

to the ``PollsApp`` class.

Any page that is attached to the ``Polls`` application will now have sub-menu
items for each of the Polls in the database.

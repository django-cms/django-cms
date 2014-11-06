#############################
Extending the navigation menu
#############################

You may have noticed that while our Polls application has been integrated into
the CMS, with plugins, toolbar menu items and so on, the site's navigation menu
is still only determined by django CMS Pages.

We can hook into the django CMS menu system to add our own nodes to that
navigation menu.

For this we need a file called ``menu.py`` in the Polls application::

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _

    from cms.menu_bases import CMSAttachMenu
    from menus.base import Menu, NavigationNode
    from menus.menu_pool import menu_pool

    from .models import Poll

    class PollsMenu(CMSAttachMenu):
        name = _("Polls Menu")  # give the menu a name this is required.

        def get_nodes(self, request):
            """
            This method is used to build the menu tree.
            """
            nodes = []
            for poll in Poll.objects.all():
                # the menu tree consists of NavigationNode instances
                # Each NavigationNode takes a label as its first argument, a URL as
                # its second argument and a (for this tree) unique id as its third
                # argument.
                node = NavigationNode(
                    poll.question,
                    reverse('polls:detail', args=(poll.pk,)),
                    poll.pk
                )
                nodes.append(node)
            return nodes

    menu_pool.register_menu(PollsMenu) # register the menu.

What's happening here:

* we define a ``PollsMenu`` class, and register it
* we give the class a ``name`` attribute
* in its ``get_nodes()`` method, we build and return a list of nodes, where:
* first we get all the ``Poll`` objects
* ... and then create a ``NavigationNode`` object from each one
* ... and return a list of these ``NavigationNodes``

This menu class is not active until attached to the AppHook we created earlier.
So open your ``cms_app.py`` and add::

    menus = [PollsMenu]

to the ``PollsApp`` class.

Now, any page that is attached to the ``Polls`` application have, below its
own node in the navigation menu, a node for each of the Polls in the database.

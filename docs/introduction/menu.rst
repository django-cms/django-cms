#############################
Extending the navigation menu
#############################

You may have noticed that while our Polls application has been integrated into
the CMS, with plugins, toolbar menu items and so on, the site's navigation menu
is still only determined by django CMS Pages.

We can hook into the django CMS menu system to add our own nodes to that
navigation menu.


**************************
Create the navigation menu
**************************

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

This menu class won't actually do anything until attached to a page. In the *Advanced settings* of the page to which
you attached the apphook earlier, select "Polls Menu" from the list of *Attached menu* options, and save once more.
(You could add the menu to any page, but it makes most sense to add it to this page.)

.. image:: /introduction/images/attach-menu.png
   :alt: select the 'Polls Menu'
   :width: 400
   :align: center

You can force the menu to be added automatically to the page by the apphook if you consider this appropriate. See
:ref:`apphook_menus` for information on how to do that.

..  note::

    The point here is to illustrate the basic principles. In this actual case, note that:

    * If you're going to use sub-pages, you'll need to improve the menu styling to make it work a
      bit better.
    * Since the Polls page lists all the Polls in it anyway, this isn't really the most practical
      addition to the menu.

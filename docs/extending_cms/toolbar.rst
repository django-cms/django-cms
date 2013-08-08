#####################
Extending the Toolbar
#####################

.. versionadded:: 3.0

You can add and remove items to the toolbar. This allows you to integrate your
application in the frontend editing mode of django CMS and provide your users
with a streamlined editing experience.

For the toolbar API reference, please refer to :ref:`toolbar-api-reference`.


***********
Registering
***********

There are two ways to control what gets shown in the toolbar. 

One is the :setting:`CMS_TOOLBARS`. This gives you full control over which
classes are loaded, but requires that you specify them all manually.

The other is to provide ``cms_toolbar.py`` files in your apps, which will be
automatically loaded as long :setting:`CMS_TOOLBARS` is not set (or set to
``None``).

If you use the automated way, your ``cms_toolbar.py`` file should contain
classes that extend from ``cms.toolbar_base.CMSToolbar`` and are registered using :meth:`cms.toolbar_pool.toolbar_pool.register`.
The register function can be used as a decorator.

These have four attributes:
* toolbar (the toolbar object)
* request (the current request)
* is_current_app (a flag indicating whether the current request is handled by the same app as the function is in)
* app_path (the name of the app used for the current request)

This classes must implement a ``populate`` function.
The populate function will only be called if the current user is a staff user.

A simple example, registering a class that does nothing::

    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar_base import CMSToolbar

    @toolbar_pool.register
    class MoopModifier(CMSToolbar):

        def populate(self):
            pass



************
Adding items
************

Items can be added through the various :ref:`APIs <toolbar-api-reference>`
exposed by the toolbar and its items. 

To add a :class:`cms.toolbar.items.Menu` to the toolbar, use
:meth:`cms.toolbar.toolbar.CMSToolbar.get_or_create_menu` which will either add a menu if
it doesn't exist, or create it. 

Then, to add a link to your changelist that will open in the sideframe, use the
:meth:`cms.toolbar.items.ToolbarMixin.add_sideframe_item` method on the menu
object returned.

When adding items, all arguments other than the name or identifier should be
given as **keyword arguments**. This will help ensure that your custom toolbar
items survive upgrades.

Following our :doc:`extending_examples`, let's add the poll app
to the toolbar::

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


However, there's already a menu added by the CMS which provides access to
various admin views, so you might want to add your menu as a sub menu there.
To do this, you can use positional insertion coupled with the fact that
:meth:`cms.toolbar.toolbar.CMSToolbar.get_or_create_menu` will return already existing
menus::


    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _
    from cms.toolbar_pool import toolbar_pool
    from cms.toolbar.items import Break
    from cms.cms_toolbar import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
    from cms.toolbar_base import CMSToolbar

    @toolbar_pool.register
    class PollToolbar(CMSToolbar):

        def populate(self):
            admin_menu = self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, _('Site'))
            position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK)
            menu = admin_menu.get_or_create_menu('poll-menu', _('Polls'), position=position)
            url = reverse('admin:polls_poll_changelist')
            menu.add_sideframe_item(_('Poll overview'), url=url)
            admin_menu.add_break('poll-break', position=menu)



==========================
Adding items through views
==========================
Another way to add items to the toolbar is through our own views (``polls/views.py``).
This method can be useful if you need to access certain variables, in our case e.g. the
selected poll and its sub-methods::

    from django.core.urlresolvers import reverse
    from django.shortcuts import get_object_or_404, render
    from django.utils.translation import ugettext_lazy as _

    from polls.models import Poll


    def detail(request, poll_id):
        poll = get_object_or_404(Poll, pk=poll_id)

        request.toolbar.populate()
        menu = request.toolbar.get_or_create_menu('polls-app', _('Polls'))
        menu.add_modal_item(_('Change this Poll'), url=reverse('admin:polls_poll_change', args=[poll_id]))
        menu.add_sideframe_item(_('Show History of this Poll'), url=reverse('admin:polls_poll_history', args=[poll_id]))
        menu.add_sideframe_item(_('Delete this Poll'), url=reverse('admin:polls_poll_delete', args=[poll_id]))

        return render(request, 'polls/detail.html', {'poll': poll})

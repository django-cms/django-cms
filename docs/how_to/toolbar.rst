.. _toolbar_how_to:

#########################
How to extend the Toolbar
#########################

The django CMS toolbar provides an API that allows you to add, remove and manipulate toolbar items
in your own code. It helps you to integrate django CMS's frontend editing mode into your
application, and provide your users with a streamlined editing experience.

..  seealso::

    * :ref:`Extending the Toolbar <toolbar_introduction>` in the tutorial
    * :ref:`Toolbar API reference <toolbar-api-reference>`


*********************************
Create a ``cms_toolbars.py`` file
*********************************

In order to interact with the toolbar API, you need to create a
:class:`~cms.toolbar_base.CMSToolbar` sub-class in your own code, and register it.

This class should be created in your application's ``cms_toolbars.py`` file, where it will be
discovered automatically when the Django runserver starts.

You can also use the :setting:`CMS_TOOLBARS` to control which toolbar classes are loaded.

..  admonition:: Use the high-level toolbar APIs

    You will find a ``toolbar`` object in the request in your views, and you may be tempted to
    do things with it, like:

    ..  code-block:: python

        toolbar = request.toolbar
        toolbar.add_modal_button('Do not touch', dangerous_button_url)

    \- but you should not, in the same way that it is not recommended to poke tweezers into
    electrical sockets just because you can.

    Instead, you should **only** interact with the toolbar using a ``CMSToolbar`` class, and the
    :ref:`documented APIs for managing it <toolbar-api-reference>`.

    Similarly, although a generic :meth:`~cms.toolbar.items.ToolbarAPIMixin.add_item` method is
    available, we provide higher-level methods for handling specific item types, and it is always
    recommended that you use these instead.


**********************************************
Define and register a ``CMSToolbar`` sub-class
**********************************************

..  code-block:: python

    from cms.toolbar_base import CMSToolbar
    from cms.toolbar_pool import toolbar_pool

    class MyToolbarClass(CMSToolbar):
        [...]

    toolbar_pool.register(MyToolbarClass)

The ``cms.toolbar_pool.ToolbarPool.register`` method can also be used as a decorator:

..  code-block:: python
    :emphasize-lines: 1

    @toolbar_pool.register
    class MyToolbarClass(CMSToolbar):
        [...]


********************
Populate the toolbar
********************

Two methods are available to control what will appear in the django CMS toolbar:

* ``populate()``, which is called *before* the rest of the page is rendered
* ``post_template_populate()``, which is called *after* the page's template is rendered

The latter method allows you to manage the toolbar based on the contents of the page, such as the
state of plugins or placeholders, but unless you need to do this, you should opt for the more
simple ``populate()`` method.

..  code-block:: python
    :emphasize-lines: 3-5

    class MyToolbar(CMSToolbar):

        def populate(self):

            # add items to the toolbar

Now you have to decide exactly what items will appear in your toolbar. These can include:

* :ref:`menus <create-toolbar-menu>`
* :ref:`buttons <create-toolbar-button>` and button lists
* various other toolbar items


Add links and buttons to the toolbar
====================================

You can add links and buttons as entries to a menu instance, using the various
``add_`` methods.

====================== ============================================================= ===========================================================
Action                 Text link variant                                             Button variant
====================== ============================================================= ===========================================================
Open link              :meth:`~cms.toolbar.items.ToolbarAPIMixin.add_link_item`      :meth:`~cms.toolbar.toolbar.CMSToolbar.add_button`
Open link in sideframe :meth:`~cms.toolbar.items.ToolbarAPIMixin.add_sideframe_item` :meth:`~cms.toolbar.toolbar.CMSToolbar.add_sideframe_button`
Open link in modal     :meth:`~cms.toolbar.items.ToolbarAPIMixin.add_modal_item`     :meth:`~cms.toolbar.toolbar.CMSToolbar.add_modal_button`
POST action            :meth:`~cms.toolbar.items.ToolbarAPIMixin.add_ajax_item`
====================== ============================================================= ===========================================================

The basic form for using any of these is:

..  code-block:: python

    def populate(self):

        self.toolbar.add_link_item( # or add_button(), add_modal_item(), etc
            name='A link',
            url=url
            )

Note that although these toolbar items may take various positional arguments in their methods, **we
strongly recommend using named arguments**, as above. This will help ensure that your own toolbar
classes and methods survive upgrades. See the reference documentation linked to in the table above
for details of the signature of each method.


Opening a URL in an iframe
--------------------------

A common case is to provide a URL that opens in a sideframe or modal dialog on the same page.
*Administration...* in the site menu, that opens the Django admin in a sideframe, is a good
example of this. Both the sideframe and modal are HTML iframes.

A typical use for a sideframe is to display an admin list (similar to that used in the
:ref:`tutorial example <add-nodes-to-polls-menu>`):

..  code-block:: python
    :emphasize-lines: 1, 8-11

    from cms.utils.urlutils import admin_reverse
    [...]

    class PollToolbar(CMSToolbar):

        def populate(self):

            self.toolbar.add_sideframe_item(
                name='Poll list',
                url=admin_reverse('polls_poll_changelist')
                )

A typical use for a modal item is to display the admin for a model instance:

..  code-block:: python

        self.toolbar.add_modal_item(name='Add new poll', url=admin_reverse('polls_poll_add'))

However, you are not restricted to these examples, and you may open any suitable resource inside
the modal or sideframe. Note that protocols may need to match and the requested resource must allow
it.


..  _create-toolbar-button:

Adding buttons to the toolbar
-----------------------------

A button is a sub-class of :class:`cms.toolbar.items.Button`

Buttons can also be added in a list - a :class:`~cms.toolbar.items.ButtonList` is a group of
visually-linked buttons.

..  code-block:: python
    :emphasize-lines: 3-5

    def populate(self):

        button_list = self.toolbar.add_button_list()
        button_list.add_button(name='Button 1', url=url_1)
        button_list.add_button(name='Button 2', url=url_2)


..  _create-toolbar-menu:

Create a toolbar menu
=====================

The text link items described above can also be added as nodes to menus in the toolbar.

A menu is an instance of :class:`cms.toolbar.items.Menu`. In your ``CMSToolbar`` sub-class, you can
either create a menu, or identify one that already exists (in order to add new items to it, for
example), in the ``populate()`` or ``post_template_populate()`` methods, using
:meth:`~cms.toolbar.toolbar.CMSToolbar.get_or_create_menu`.

..  code-block:: python

    def populate(self):
        menu = self.toolbar.get_or_create_menu(
            key='polls_cms_integration',
            verbose_name='Polls'
            )

The ``key`` is unique menu identifier; ``verbose_name`` is what will be displayed in the menu. If
you know a menu already exists, you can obtain it with
:meth:`~cms.toolbar.toolbar.CMSToolbar.get_menu`.

..  note::

    It's recommended to namespace your ``key`` with the application name. Otherwise, another
    application could unexpectedly interfere with your menu.

Once you have your menu, you can add items to it in much the same way that you add them to the
toolbar. For example:

..  code-block:: python
    :emphasize-lines: 4-7

    def populate(self):
        menu = [...]

        menu.add_sideframe_item(
            name='Poll list',
            url=admin_reverse('polls_poll_changelist')
        )


To add a menu divider
---------------------

:meth:`~cms.toolbar.items.SubMenu.add_break` will place a
:class:`~cms.toolbar.items.Break`, a visual divider, in a menu list, to allow grouping of items.
For example:

..  code-block:: python

    menu.add_break(identifier='settings_section')


To add a sub-menu
-----------------

A sub-menu is a menu that belongs to another ``Menu``:

..  code-block:: python
    :emphasize-lines: 4-7

    def populate(self):
        menu = [...]

        submenu = menu.get_or_create_menu(
            key='sub_menu_key',
            verbose_name='My sub-menu'
            )

You can then add items to the sub-menu in the same way as in the examples above. Note that a
sub-menu is an instance of :class:`~cms.toolbar.items.SubMenu`, and may not itself have further
sub-menus.


.. _finding_toolbar_items:

******************************
Finding existing toolbar items
******************************

``get_or_create_menu()`` and ``get_menu()``
===========================================

A number of methods and useful constants exist to get hold of and manipulate existing toolbar
items. For example, to find (using ``get_menu()``) and rename the *Site* menu:

..  code-block:: python

    from cms.cms_toolbars import ADMIN_MENU_IDENTIFIER

    class ManipulativeToolbar(CMSToolbar):

        def populate(self):

            admin_menu = self.toolbar.get_menu(ADMIN_MENU_IDENTIFIER)

            admin_menu.name = "Site"

``get_or_create_menu()`` will equally well find the same menu, and also has the advantages that:

* it can update the item's attributes itself
  (``self.toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Site')``)
* if the item doesn't exist, it will create it rather than raising an error.


``find_items()`` and ``find_first()``
=====================================

Search for items by their type:

..  code-block:: python

    def populate(self):

        self.toolbar.find_items(item_type=LinkItem)

will find all ``LinkItem``\s in the toolbar (but not for example in the menus in the toolbar - it
doesn't search *other* items in the toolbar for items of their own).

:meth:`~cms.toolbar.items.ToolbarAPIMixin.find_items` returns a list of
:class:`~cms.toolbar.items.ItemSearchResult` objects;
:meth:`~cms.toolbar.items.ToolbarAPIMixin.find_first` returns the first object in that list. They
share similar behaviour so the examples here will use ``find_items()`` only.

The ``item_type`` argument is always required, but you can refine the search by using their other
attributes, for example::

    self.toolbar.find_items(Menu, disabled=True))

Note that you can use these two methods to search ``Menu`` and ``SubMenu`` classes for items too.


.. _toolbar_control_item_position:

********************************************
Control the position of items in the toolbar
********************************************

Methods to add menu items to the toolbar take an optional :option:`position` argument, that can be
used to control where the item will be inserted.

By default (``position=None``) the item will be inserted after existing items in the same level of
the hierarchy (a new sub-menu will become the last sub-menu of the menu, a new menu will be become
the last menu in the toolbar, and so on).

A position of ``0`` will insert the item before all the others.

If you already have an object, you can use that as a reference too. For example:

..  code-block:: python

    def populate(self):

        link = self.toolbar.add_link_item('Link', url=link_url)
        self.toolbar.add_button('Button', url=button_url, position=link)

will add the new button before the link item.

Finally, you can use a :class:`~cms.toolbar.items.ItemSearchResult` as a position:

..  code-block:: python

    def populate(self):

        self.toolbar.add_link_item('Link', url=link_url)

        link = self.toolbar.find_first(LinkItem)

        self.toolbar.add_button('Button', url=button_url, position=link)

and since the ``ItemSearchResult`` can be cast to an integer, you could even do:

    self.toolbar.add_button('Button', url=button_url, position=link+1)


****************************************
Control how and when the toolbar appears
****************************************

By default, your :class:`~cms.toolbar_base.CMSToolbar` sub-class will be active (i.e. its
``populate`` methods will be called) in the toolbar on every page, when the user ``is_staff``.
Sometimes however a ``CMSToolbar`` sub-class should only populate the toolbar when visiting pages
associated with a particular application.

A ``CMSToolbar`` sub-class has a useful attribute that can help determine whether a toolbar should
be activated. ``is_current_app`` is ``True`` when the application containing the toolbar class
matches the application handling the request.

This allows you to activate it selectively, for example:

..  code-block:: python
    :emphasize-lines: 3-4

    def populate(self):

        if not self.is_current_app:
            return

        [...]

If your toolbar class is in another application than the one you want it to be active for,
you can list any applications it should support when you create the class:

..  code-block:: python

    supported_apps = ['some_app']

``supported_apps`` is a tuple of application dotted paths (e.g: ``supported_apps =
('whatever.path.app', 'another.path.app')``.

The attribute ``app_path`` will contain the name of the application handling the current request
- if ``app_path`` is in ``supported_apps``, then ``is_current_app`` will be ``True``.


*****************************
Modifying an existing toolbar
*****************************

If you need to modify an existing toolbar (say to change an attribute or the behaviour of a method)
you can do this by creating a sub-class of it that implements the required changes, and registering
that instead of the original.

The original can be unregistered using ``toolbar_pool.unregister()``, as in the example below.
Alternatively if you originally invoked the toolbar class using :setting:`CMS_TOOLBARS`, you will
need to modify that to refer to the new one instead.

An example, in which we unregister the original and register our own::


    from cms.toolbar_pool import toolbar_pool
    from third_party_app.cms_toolbar import ThirdPartyToolbar

    @toolbar_pool.register
    class MyBarToolbar(ThirdPartyToolbar):
        [...]

    toolbar_pool.unregister(ThirdPartyToolbar)


.. _url_changes:

**********************************
Detecting URL changes to an object
**********************************

If you want to watch for object creation or editing of models and redirect after they have been
added or changed add a ``watch_models`` attribute to your toolbar.

Example::

    class PollToolbar(CMSToolbar):

        watch_models = [Poll]

        def populate(self):
            ...

After you add this every change to an instance of ``Poll`` via sideframe or modal window will
trigger a redirect to the URL of the poll instance that was edited, according to the toolbar
status:

* in *draft* mode the ``get_draft_url()`` is returned (or ``get_absolute_url()`` if the former
  does not exist)
* in *live* mode, and the method exists, ``get_public_url()`` is returned.


********
Frontend
********

If you need to interact with the toolbar, or otherwise account for it in your site's frontend code,
it provides CSS and JavaScript hooks for you to use.

It will add various classes to the page's ``<html>`` element:

* ``cms-ready``, when the toolbar is ready
* ``cms-toolbar-expanded``, when the toolbar is fully expanded
* ``cms-toolbar-expanding`` and ``cms-toolbar-collapsing`` during toolbar animation.

The toolbar also fires a JavaScript event called ``cms-ready`` on the document.
You can listen to this event using jQuery::

    CMS.$(document).on('cms-ready', function () { ... });

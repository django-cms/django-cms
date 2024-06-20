import json
from abc import ABCMeta
from collections import defaultdict

from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.functional import Promise

from cms.constants import LEFT, REFRESH_PAGE, RIGHT, URL_CHANGE
from cms.utils.compat import DJANGO_4_2


class ItemSearchResult:
    """
    Returned by the find APIs in :class:`ToolbarAPIMixin`.

    An ``ItemSearchResult`` will have two useful attributes:

    .. attribute:: item

        The item found.

    .. attribute:: index

        The index of the item (its position amongst the other items).

    The ``ItemSearchResult`` itself can be cast to an integer, and supports addition and
    subtraction of numbers. See the :option:`position` parameter for more details, and
    :ref:`toolbar_control_item_position` for examples.
    """
    def __init__(self, item, index):
        self.item = item
        self.index = index

    def __add__(self, other):
        return ItemSearchResult(self.item, self.index + other)

    def __sub__(self, other):
        return ItemSearchResult(self.item, self.index - other)

    def __int__(self):
        return self.index


if DJANGO_4_2:
    def may_be_lazy(thing):
        if isinstance(thing, Promise):
            return thing._proxy____args[0]
        else:
            return thing
else:
    def may_be_lazy(thing):
        if isinstance(thing, Promise):
            return thing._args[0]
        else:
            return thing


class ToolbarAPIMixin(metaclass=ABCMeta):
    """
    Provides APIs used by :class:`~cms.toolbar.toolbar.CMSToolbar` and :class:`Menu`.
    """
    REFRESH_PAGE = REFRESH_PAGE
    URL_CHANGE = URL_CHANGE
    LEFT = LEFT
    RIGHT = RIGHT

    def __init__(self):
        self.items = []
        self.menus = {}
        self._memo = defaultdict(list)

    def _memoize(self, item):
        self._memo[item.__class__].append(item)

    def _unmemoize(self, item):
        self._memo[item.__class__].remove(item)

    def _item_position(self, item):
        return self.items.index(item)

    def _add_item(self, item, position):
        if position is not None:
            self.items.insert(position, item)
        else:
            self.items.append(item)

    def _remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
        else:
            raise KeyError("Item %r not found" % item)

    def get_item_count(self):
        """Returns the number of items in the menu."""
        return len(self.items)

    def add_item(self, item, position=None):
        """Adds an item (which must be a subclass of :class:`~cms.toolbar.items.BaseItem`), and
        returns it. This is a low-level API, and you should always use one of the built-in
        object-specific methods to add items in preference if possible, using this method **only**
        for custom item classes."""
        if not isinstance(item, BaseItem):
            raise ValueError("Items must be subclasses of cms.toolbar.items.BaseItem, %r isn't" % item)
        if isinstance(position, ItemSearchResult):
            position = position.index
        elif isinstance(position, BaseItem):
            position = self._item_position(position)
        elif not (position is None or isinstance(position, (int,))):
            raise ValueError(
                "Position must be None, an integer, an item or an ItemSearchResult, got %r instead" % position
            )
        self._add_item(item, position)
        self._memoize(item)
        return item

    def find_items(self, item_type, **attributes):
        """Returns a list of :class:`~cms.toolbar.items.ItemSearchResult` objects matching all items of ``item_type``
        (e.g. ``LinkItem``)."""
        results = []
        attr_items = attributes.items()
        notfound = object()
        for candidate in self._memo[item_type]:
            if all(may_be_lazy(getattr(candidate, key, notfound)) == value for key, value in attr_items):
                results.append(ItemSearchResult(candidate, self._item_position(candidate)))
        return results

    def find_first(self, item_type, **attributes):
        """Returns the first :class:`~cms.toolbar.items.ItemSearchResult` that matches the search, or ``None``.
        The search strategy is the same as in :meth:`find_items`. The return value of this method is
        safe to use as the :option:`position` argument of the various APIs to add items."""
        try:
            return self.find_items(item_type, **attributes)[0]
        except IndexError:
            return None

    #
    # This will only work if it is used to determine the insert position for
    # all items in the same menu.
    #
    def get_alphabetical_insert_position(self, new_menu_name, item_type,
                                         default=0):
        results = self.find_items(item_type)

        # No items yet? Use the default value provided
        if not len(results):
            return default

        last_position = 0

        for result in sorted(results, key=lambda x: x.item.name):
            if result.item.name > new_menu_name:
                return result.index

            if result.index > last_position:
                last_position = result.index
        else:
            return last_position + 1

    def remove_item(self, item):
        self._remove_item(item)
        self._unmemoize(item)

    def add_sideframe_item(self, name, url, active=False, disabled=False,
                           extra_classes=None, on_close=None, side=LEFT, position=None):
        """Adds a :class:`~cms.toolbar.items.SideframeItem` that opens ``url`` in the sideframe and returns it."""

        item = SideframeItem(
            name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            on_close=on_close,
            side=side,
        )
        self.add_item(item, position=position)
        return item

    def add_modal_item(self, name, url, active=False, disabled=False,
                       extra_classes=None, on_close=REFRESH_PAGE, side=LEFT, position=None):
        """Similar to :meth:`add_sideframe_item`, but adds a :class:`~cms.toolbar.items.ModalItem` that opens the
        ``url`` in a modal dialog instead of the sideframe, and returns it."""

        item = ModalItem(
            name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            on_close=on_close,
            side=side,
        )
        self.add_item(item, position=position)
        return item

    def add_link_item(self, name, url, active=False, disabled=False,
                      extra_classes=None, side=LEFT, position=None):
        """Adds a :class:`~cms.toolbar.items.LinkItem` that opens ``url``, and returns it."""

        item = LinkItem(
            name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            side=side
        )
        self.add_item(item, position=position)
        return item

    def add_ajax_item(self, name, action, active=False, disabled=False,
                      extra_classes=None, data=None, question=None,
                      side=LEFT, position=None, on_success=None, method='POST'):
        """Adds :class:`~cms.toolbar.items.AjaxItem` that sends a POST request to ``action`` with ``data``, and returns
        it. ``data`` should be ``None`` or a dictionary. The CSRF token will automatically be added
        to the item.

        If a string is provided for ``question``, it will be presented to the user to allow
        confirmation before the request is sent."""

        item = AjaxItem(
            name, action, self.csrf_token,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            data=data,
            question=question,
            side=side,
            on_success=on_success,
            method=method,
        )
        self.add_item(item, position=position)
        return item


class BaseItem(metaclass=ABCMeta):
    """
    All toolbar items inherit from ``BaseItem``. If you need to create a custom toolbar item,
    subclass ``BaseItem``.
    """
    toolbar = None
    #: Must be set by subclasses and point to a Django template
    template = None

    def __init__(self, side=LEFT):
        self.side = side

    @property
    def right(self):
        return self.side is RIGHT

    def render(self):
        """
        Renders the item and returns it as a string. By default, calls
        :meth:`get_context` and renders :attr:`template` with the context
        returned.
        """
        if self.toolbar:
            template = self.toolbar.templates.get_cached_template(self.template)
            return template.render(self.get_context())
        # Backwards compatibility
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        """Returns the context (as dictionary) for this item."""
        return {}


class TemplateItem(BaseItem):

    def __init__(self, template, extra_context=None, side=LEFT):
        super().__init__(side)
        self.template = template
        self.extra_context = extra_context

    def get_context(self):
        if self.extra_context:
            return self.extra_context
        return {}


class SubMenu(ToolbarAPIMixin, BaseItem):
    """
    A child of a :class:`Menu`. Use a :meth:`Menu.get_or_create_menu
    <cms.toolbar.items.Menu.get_or_create_menu>` method to create a ``SubMenu``
    instance. Can be added to ``Menu``.
    """
    template = "cms/toolbar/items/menu.html"
    sub_level = True
    active = False

    def __init__(self, name, csrf_token, disabled=False, side=LEFT):
        ToolbarAPIMixin.__init__(self)
        BaseItem.__init__(self, side)
        self.name = name
        self.disabled = disabled
        self.csrf_token = csrf_token

    def __repr__(self):
        return '<Menu:%s>' % force_str(self.name)

    def add_break(self, identifier=None, position=None):
        """Adds a visual break in the menu, at :option:`position`, and returns it. ``identifier`` may
        be used to make this item searchable."""
        item = Break(identifier)
        self.add_item(item, position=position)
        return item

    def get_items(self):
        items = self.items
        for item in items:
            item.toolbar = self.toolbar
            if hasattr(item, 'disabled'):
                item.disabled = self.disabled or item.disabled
        return items

    def get_context(self):
        return {
            'active': self.active,
            'disabled': self.disabled,
            'items': self.get_items(),
            'title': self.name,
            'sub_level': self.sub_level
        }


class Menu(SubMenu):
    """
    Provides a menu in the toolbar. Use a :meth:`CMSToolbar.get_or_create_menu
    <cms.toolbar.toolbar.CMSToolbar.get_or_create_menu>` method to create a ``Menu``
    instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`.
    """
    sub_level = False

    def get_or_create_menu(self, key, verbose_name, disabled=False, side=LEFT, position=None):
        """Adds a new sub-menu, at :option:`position`, and returns a :class:`SubMenu`."""
        if key in self.menus:
            return self.menus[key]
        menu = SubMenu(verbose_name, self.csrf_token, disabled=disabled, side=side)
        self.menus[key] = menu
        self.add_item(menu, position=position)
        return menu


class LinkItem(BaseItem):
    """
    Sends a GET request. Use an :class:`~ToolbarAPIMixin.add_link_item` method to create a
    ``LinkItem`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`,
    :class:`~cms.toolbar.items.Menu`, :class:`~cms.toolbar.items.SubMenu`.
    """
    template = "cms/toolbar/items/item_link.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, side=LEFT):
        super().__init__(side)
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<LinkItem:%s>' % force_str(self.name)

    def get_context(self):
        return {
            'url': self.url,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }


class FrameItem(BaseItem):
    """
    Base class for :class:`~cms.toolbar.items.ModalItem` and :class:`~cms.toolbar.items.SideframeItem`.
    Frame items have three dots besides their name indicating that some frame or dialog will open
    when selected.
    """
    # Be sure to define the correct template

    def __init__(self, name, url, active=False, disabled=False,
                 extra_classes=None, on_close=None, side=LEFT):
        super().__init__(side)
        self.name = "%s..." % force_str(name)
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []
        self.on_close = on_close

    def __repr__(self):
        # Should be overridden
        return '<FrameItem:%s>' % force_str(self.name)

    def get_context(self):
        return {
            'url': self.url,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
            'on_close': self.on_close,
        }


class SideframeItem(FrameItem):
    """
    Sends a GET request; loads response in a sideframe. Use an
    :class:`~ToolbarAPIMixin.add_sideframe_item` method to create a ``SideframeItem`` instance. Can
    be added to :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.Menu`,
    :class:`~cms.toolbar.items.SubMenu`.
    """
    template = "cms/toolbar/items/item_sideframe.html"

    def __repr__(self):
        return '<SideframeItem:%s>' % force_str(self.name)


class ModalItem(FrameItem):
    """
    Sends a GET request; loads response in a modal window. Use an
    :class:`~ToolbarAPIMixin.add_modal_item` method to create a ``ModalItem`` instance. Can be
    added to :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.Menu`,
    :class:`~cms.toolbar.items.SubMenu`.
    """
    template = "cms/toolbar/items/item_modal.html"

    def __repr__(self):
        return '<ModalItem:%s>' % force_str(self.name)


class AjaxItem(BaseItem):
    """
    Sends a POST request. Use an :class:`~ToolbarAPIMixin.add_ajax_item` method to create a
    ``AjaxItem`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`,
    :class:`~cms.toolbar.items.Menu`, :class:`~cms.toolbar.items.SubMenu`.

    """
    template = "cms/toolbar/items/item_ajax.html"

    def __init__(self, name, action, csrf_token, data=None, active=False,
                 disabled=False, extra_classes=None,
                 question=None, side=LEFT, on_success=None, method='POST'):
        super().__init__(side)
        self.name = name
        self.action = action
        self.active = active
        self.disabled = disabled
        self.csrf_token = csrf_token
        self.data = data or {}
        self.extra_classes = extra_classes or []
        self.question = question
        self.on_success = on_success
        self.method = method

    def __repr__(self):
        return '<AjaxItem:%s>' % force_str(self.name)

    def get_context(self):
        data = self.data.copy()

        if self.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            data['csrfmiddlewaretoken'] = self.csrf_token

        return {
            'action': self.action,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
            'data': json.dumps(data),
            'question': self.question,
            'on_success': self.on_success,
            'method': self.method,
        }


class Break(BaseItem):
    """
    A visual break in a menu. Use an :class:`~cms.toolbar.items.SubMenu.add_break` method to create
    a ``Break`` instance. Can be added to :class:`~cms.toolbar.items.Menu`,
    :class:`~cms.toolbar.items.SubMenu`.

    """
    template = "cms/toolbar/items/break.html"

    def __init__(self, identifier=None):
        self.identifier = identifier


class BaseButton(metaclass=ABCMeta):
    toolbar = None
    template = None

    def render(self):
        if self.toolbar:
            template = self.toolbar.templates.get_cached_template(self.template)
            return template.render(self.get_context())
        # Backwards compatibility
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        return {}


class Button(BaseButton):
    """
    Sends a GET request. Use a :meth:`CMSToolbar.add_button
    <cms.toolbar.toolbar.CMSToolbar.add_button>` or :meth:`ButtonList.add_button` method to create
    a ``Button`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`,
    :class:`~cms.toolbar.items.ButtonList`.
    """
    template = "cms/toolbar/items/button.html"

    def __init__(self, name, url, active=False, disabled=False,
                 extra_classes=None):
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<Button:%s>' % force_str(self.name)

    def get_context(self):
        return {
            'name': self.name,
            'url': self.url,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }


class ModalButton(Button):
    """
    Sends a GET request. Use a :meth:`CMSToolbar.add_modal_button
    <cms.toolbar.toolbar.CMSToolbar.add_modal_button>` or :meth:`ButtonList.add_modal_button`
    method to create a ``ModalButton`` instance. Can be added to
    :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.ButtonList`.
    """
    template = "cms/toolbar/items/button_modal.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, on_close=None):
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []
        self.on_close = on_close

    def __repr__(self):
        return '<ModalButton:%s>' % force_str(self.name)

    def get_context(self):
        return {
            'name': self.name,
            'url': self.url,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
            'on_close': self.on_close,
        }


class SideframeButton(ModalButton):
    """
    Sends a GET request. Use a :meth:`CMSToolbar.add_sideframe_button
    <cms.toolbar.toolbar.CMSToolbar.add_sideframe_button>` or
    :meth:`ButtonList.add_sideframe_button` method to create a ``SideframeButton`` instance. Can be
    added to :class:`~cms.toolbar.toolbar.CMSToolbar`, :class:`~cms.toolbar.items.ButtonList`.
    """
    template = "cms/toolbar/items/button_sideframe.html"

    def __repr__(self):
        return '<SideframeButton:%s>' % force_str(self.name)


class ButtonList(BaseItem):
    """
    A visually-connected list of one or more buttons. Use an
    :meth:`~cms.toolbar.toolbar.CMSToolbar.add_button_list` method to create a
    ``ButtonList`` instance. Can be added to :class:`~cms.toolbar.toolbar.CMSToolbar`.
    """
    template = "cms/toolbar/items/button_list.html"

    def __init__(self, identifier=None, extra_classes=None, side=LEFT):
        super().__init__(side)
        self.extra_classes = extra_classes or []
        self.buttons = []
        self.identifier = identifier

    def __repr__(self):
        return '<ButtonList:%s>' % self.identifier

    def add_item(self, item):
        if not isinstance(item, Button):
            raise ValueError("Expected instance of cms.toolbar.items.Button, got %r instead" % item)
        self.buttons.append(item)

    def add_button(self, name, url, active=False, disabled=False,
                   extra_classes=None):
        """Adds a :class:`Button` to the list of buttons and returns it."""

        item = Button(
            name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes
        )
        self.buttons.append(item)
        return item

    def add_modal_button(self, name, url, active=False, disabled=False, extra_classes=None, on_close=REFRESH_PAGE):
        """Adds a :class:`~cms.toolbar.items.ModalButton` to the button list and returns it."""

        item = ModalButton(
            name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            on_close=on_close,
        )
        self.buttons.append(item)
        return item

    def add_sideframe_button(self, name, url, active=False, disabled=False, extra_classes=None, on_close=None):
        """Adds a :class:`~cms.toolbar.items.SideframeButton` to the button list and returns it."""

        item = SideframeButton(
            name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            on_close=on_close,
        )
        self.buttons.append(item)
        return item

    def get_buttons(self):
        """Yields all buttons in the button list"""
        for button in self.buttons:
            button.toolbar = self.toolbar
            yield button

    def get_context(self):
        context = {
            'buttons': list(self.get_buttons()),
            'extra_classes': self.extra_classes
        }

        if self.toolbar:
            context['cms_structure_url'] = self.toolbar.get_object_structure_url()
        return context


class Dropdown(ButtonList):

    template = "cms/toolbar/items/dropdown.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.primary_button = None

    def __repr__(self):
        return '<Dropdown:%s>' % force_str(self.name)

    def add_primary_button(self, button):
        self.primary_button = button

    def get_buttons(self):
        for button in self.buttons:
            button.toolbar = self.toolbar
            button.is_in_dropdown = True
            yield button

    def get_context(self):
        return {
            'primary_button': self.primary_button,
            'buttons': list(self.get_buttons()),
            'extra_classes': self.extra_classes,
        }


class DropdownToggleButton(BaseButton):
    template = "cms/toolbar/items/dropdown_button.html"
    has_no_action = True

    def __init__(self, name, active=False, disabled=False,
                 extra_classes=None):
        self.name = name
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<DropdownToggleButton:%s>' % force_str(self.name)

    def get_context(self):
        return {
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }

import json
from abc import ABCMeta
from collections import defaultdict

from django.template.loader import render_to_string
from django.utils import six
from django.utils.encoding import force_text
from django.utils.functional import Promise

from cms.constants import RIGHT, LEFT, REFRESH_PAGE, URL_CHANGE


class ItemSearchResult(object):
    def __init__(self, item, index):
        self.item = item
        self.index = index

    def __add__(self, other):
        return ItemSearchResult(self.item, self.index + other)

    def __sub__(self, other):
        return ItemSearchResult(self.item, self.index - other)

    def __int__(self):
        return self.index


def may_be_lazy(thing):
    if isinstance(thing, Promise):
        return thing._proxy____args[0]
    else:
        return thing


class ToolbarAPIMixin(six.with_metaclass(ABCMeta)):
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
        return len(self.items)

    def add_item(self, item, position=None):
        if not isinstance(item, BaseItem):
            raise ValueError("Items must be subclasses of cms.toolbar.items.BaseItem, %r isn't" % item)
        if isinstance(position, ItemSearchResult):
            position = position.index
        elif isinstance(position, BaseItem):
            position = self._item_position(position)
        elif not (position is None or isinstance(position, (int,))):
            raise ValueError("Position must be None, an integer, an item or an ItemSearchResult, got %r instead" % position)
        self._add_item(item, position)
        self._memoize(item)
        return item

    def find_items(self, item_type, **attributes):
        results = []
        attr_items = attributes.items()
        notfound = object()
        for candidate in self._memo[item_type]:
            if all(may_be_lazy(getattr(candidate, key, notfound)) == value for key, value in attr_items):
                results.append(ItemSearchResult(candidate, self._item_position(candidate)))
        return results

    def find_first(self, item_type, **attributes):
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
        item = SideframeItem(name, url,
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
        item = ModalItem(name, url,
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
        item = LinkItem(name, url,
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
        item = AjaxItem(name, action, self.csrf_token,
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


class BaseItem(six.with_metaclass(ABCMeta)):
    toolbar = None
    template = None

    def __init__(self, side=LEFT):
        self.side = side

    @property
    def right(self):
        return self.side is RIGHT

    def render(self):
        if self.toolbar:
            template = self.toolbar.templates.get_cached_template(self.template)
            return template.render(self.get_context())
        # Backwards compatibility
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        return {}


class TemplateItem(BaseItem):

    def __init__(self, template, extra_context=None, side=LEFT):
        super(TemplateItem, self).__init__(side)
        self.template = template
        self.extra_context = extra_context

    def get_context(self):
        if self.extra_context:
            return self.extra_context
        return {}


class SubMenu(ToolbarAPIMixin, BaseItem):
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
        return '<Menu:%s>' % force_text(self.name)

    def add_break(self, identifier=None, position=None):
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
    sub_level = False

    def get_or_create_menu(self, key, verbose_name, disabled=False, side=LEFT, position=None):
        if key in self.menus:
            return self.menus[key]
        menu = SubMenu(verbose_name, self.csrf_token, disabled=disabled, side=side)
        self.menus[key] = menu
        self.add_item(menu, position=position)
        return menu


class LinkItem(BaseItem):
    template = "cms/toolbar/items/item_link.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, side=LEFT):
        super(LinkItem, self).__init__(side)
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<LinkItem:%s>' % force_text(self.name)

    def get_context(self):
        return {
            'url': self.url,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }


class FrameItem(BaseItem):
    # Be sure to define the correct template

    def __init__(self, name, url, active=False, disabled=False,
                 extra_classes=None, on_close=None, side=LEFT):
        super(FrameItem, self).__init__(side)
        self.name = "%s..." % force_text(name)
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []
        self.on_close = on_close

    def __repr__(self):
        # Should be overridden
        return '<FrameItem:%s>' % force_text(self.name)

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
    template = "cms/toolbar/items/item_sideframe.html"

    def __repr__(self):
        return '<SideframeItem:%s>' % force_text(self.name)


class ModalItem(FrameItem):
    template = "cms/toolbar/items/item_modal.html"

    def __repr__(self):
        return '<ModalItem:%s>' % force_text(self.name)


class AjaxItem(BaseItem):
    template = "cms/toolbar/items/item_ajax.html"

    def __init__(self, name, action, csrf_token, data=None, active=False,
                 disabled=False, extra_classes=None,
                 question=None, side=LEFT, on_success=None, method='POST'):
        super(AjaxItem, self).__init__(side)
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
        return '<AjaxItem:%s>' % force_text(self.name)

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
    template = "cms/toolbar/items/break.html"

    def __init__(self, identifier=None):
        self.identifier = identifier


class BaseButton(six.with_metaclass(ABCMeta)):
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
    template = "cms/toolbar/items/button.html"

    def __init__(self, name, url, active=False, disabled=False,
                 extra_classes=None):
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<Button:%s>' % force_text(self.name)

    def get_context(self):
        return {
            'name': self.name,
            'url': self.url,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }


class ModalButton(Button):
    template = "cms/toolbar/items/button_modal.html"

    def __init__(self, name, url, active=False, disabled=False,  extra_classes=None, on_close=None):
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []
        self.on_close = on_close

    def __repr__(self):
        return '<ModalButton:%s>' % force_text(self.name)

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
    template = "cms/toolbar/items/button_sideframe.html"

    def __repr__(self):
        return '<SideframeButton:%s>' % force_text(self.name)


class ButtonList(BaseItem):
    template = "cms/toolbar/items/button_list.html"

    def __init__(self, identifier=None, extra_classes=None, side=LEFT):
        super(ButtonList, self).__init__(side)
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
        item = Button(name, url,
                      active=active,
                      disabled=disabled,
                      extra_classes=extra_classes
        )
        self.buttons.append(item)
        return item

    def add_modal_button(self, name, url, active=False, disabled=False, extra_classes=None, on_close=REFRESH_PAGE):
        item = ModalButton(name, url,
                      active=active,
                      disabled=disabled,
                      extra_classes=extra_classes,
                      on_close=on_close,
        )
        self.buttons.append(item)
        return item

    def add_sideframe_button(self, name, url, active=False, disabled=False, extra_classes=None, on_close=None):
        item = SideframeButton(name, url,
                      active=active,
                      disabled=disabled,
                      extra_classes=extra_classes,
                      on_close=on_close,
        )
        self.buttons.append(item)
        return item

    def get_buttons(self):
        for button in self.buttons:
            button.toolbar = self.toolbar
            yield button

    def get_context(self):
        context = {
            'buttons': list(self.get_buttons()),
            'extra_classes': self.extra_classes
        }

        if self.toolbar:
            context['cms_structure_on'] = self.toolbar.structure_mode_url_on
        return context


class Dropdown(ButtonList):

    template = "cms/toolbar/items/dropdown.html"

    def __init__(self, *args, **kwargs):
        super(Dropdown, self).__init__(*args, **kwargs)
        self.primary_button = None

    def __repr__(self):
        return '<Dropdown:%s>' % force_text(self.name)

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
        return '<DropdownToggleButton:%s>' % force_text(self.name)

    def get_context(self):
        return {
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }

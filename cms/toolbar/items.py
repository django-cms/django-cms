import abc
from collections import defaultdict, namedtuple
from cms.constants import RIGHT, LEFT, REFRESH
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.functional import Promise


ItemSearchResult = namedtuple('ItemSearchResult', 'item index')


def may_be_lazy(thing):
    if isinstance(thing, Promise):
        return thing._proxy____args[0]
    else:
        return thing


class ToolbarAPIMixin(object):
    __metaclass__ = abc.ABCMeta
    
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

    def _add_item(self, item):
        self.items.append(item)

    def _remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
        else:
            raise KeyError("Item %r not found" % item)

    def add_item(self, item):
        if not isinstance(item, BaseItem):
            raise ValueError("Items must be subclasses of cms.toolbar.items.BaseItem, %r isn't" % item)
        self._add_item(item)
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

    def remove_item(self, item):
        self._remove_item(item)
        self._unmemoize(item)

    def add_sideframe_item(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=False,
                 on_close=None, position=LEFT):
        item = SideframeItem(name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            close_on_url_change=close_on_url_change,
            on_close=on_close,
            position=position,
        )
        self.add_item(item)
        return item

    def add_modal_item(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=True,
                 on_close=REFRESH, position=LEFT):
        item = ModalItem(name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            close_on_url_change=close_on_url_change,
            on_close=on_close,
            position=position,
        )
        self.add_item(item)
        return item

    def add_link_item(self, name, url, active=False, disabled=False, extra_classes=None, position=LEFT):
        item = LinkItem(name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            position=position
        )
        self.add_item(item)
        return item

    def add_ajax_item(self, name, action, active=False, disabled=False, extra_classes=None, data=None, question=None,
                      position=LEFT):
        item = AjaxItem(name, action, self.csrf_token,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes,
            data=data,
            question=question,
            position=position,
        )
        self.add_item(item)
        return item


class BaseItem(object):
    __metaclass__ = abc.ABCMeta
    template = abc.abstractproperty()

    def __init__(self, position=LEFT):
        self.position = position

    @property
    def right(self):
        return self.position is RIGHT

    def render(self):
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        return {}


class Menu(ToolbarAPIMixin, BaseItem):
    template = "cms/toolbar/items/menu.html"

    def __init__(self, name, csrf_token, url='#', sub_level=False, position=LEFT):
        ToolbarAPIMixin.__init__(self)
        BaseItem.__init__(self, position)
        self.url = url
        self.name = name
        self.sub_level = sub_level
        self.csrf_token = csrf_token

    def __repr__(self):
        return '<Menu:%s>' % unicode(self.name)

    def get_menu(self, key, verbose_name, position=LEFT):
        if key in self.menus:
            return self.menus[key]
        menu = Menu(verbose_name, self.csrf_token, sub_level=True, position=position)
        self.menus[key] = menu
        self.items.append(menu)
        return menu

    def add_break(self, identifier=None):
        item = Break(identifier=identifier)
        self.add_item(item)
        return item

    def get_items(self):
        return self.items

    def get_context(self):
        return {
            'items': self.get_items(),
            'url': self.url,
            'title': self.name,
            'sub_level': self.sub_level}


class LinkItem(BaseItem):
    template = "cms/toolbar/items/item_link.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, position=LEFT):
        self.position = position
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<LinkItem:%s>' % unicode(self.name)

    def get_context(self):
        return {
            'url': self.url,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
        }


class SideframeItem(BaseItem):
    template = "cms/toolbar/items/item_sideframe.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=False,
                 on_close=REFRESH, position=LEFT):
        self.position = position
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []
        self.on_close = on_close
        self.close_on_url_change = close_on_url_change

    def __repr__(self):
        return '<SideframeItem:%s>' % unicode(self.name)

    def get_context(self):
        return {
            'url': self.url,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
            'on_close': self.on_close,
            'close_on_url_change': self.close_on_url_change,
        }


class AjaxItem(BaseItem):
    template = "cms/toolbar/items/item_ajax.html"

    def __init__(self, name, action, csrf_token, data=None, active=False, disabled=False, extra_classes=None,
                 question=None, position=LEFT):
        self.position = position
        self.name = name
        self.action = action
        self.active = active
        self.disabled = disabled
        self.csrf_token = csrf_token
        self.data = data or {}
        self.extra_classes = extra_classes or []
        self.question = question

    def __repr__(self):
        return '<AjaxItem:%s>' % unicode(self.name)

    def get_context(self):
        data = {}
        data.update(self.data)
        data[settings.CSRF_COOKIE_NAME] = self.csrf_token
        data = simplejson.dumps(data)
        return {
            'action': self.action,
            'name': self.name,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
            'data': data,
            'question': self.question
        }


class ModalItem(BaseItem):
    template = "cms/toolbar/items/item_modal.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=True,
                 on_close=REFRESH, position=LEFT):
        self.position = position
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []
        self.close_on_url_change = close_on_url_change
        self.on_close = on_close

    def __repr__(self):
        return '<ModalItem:%s>' % unicode(self.name)

    def get_context(self):
        return {
            'name': self.name,
            'url': self.url,
            'active': self.active,
            'disabled': self.disabled,
            'extra_classes': self.extra_classes,
            'close_on_url_change': self.close_on_url_change,
            'on_close': self.on_close,
        }


class Break(BaseItem):
    template = "cms/toolbar/items/break.html"

    def __init__(self, identifier=None):
        self.identifier = identifier


class Button(object):
    def __init__(self, name, url, active=False, disabled=False, extra_classes=None):
        self.name = name
        self.url = url
        self.active = active
        self.disabled = disabled
        self.extra_classes = extra_classes or []

    def __repr__(self):
        return '<Button:%s>' % unicode(self.name)


class ButtonList(BaseItem):
    template = "cms/toolbar/items/button_list.html"

    def __init__(self, extra_classes=None, position=LEFT):
        self.position = position
        self.extra_classes = extra_classes or []
        self.buttons = []

    def add_item(self, item):
        if not isinstance(item, Button):
            raise ValueError("Expected instance of cms.toolbar.items.Button, got %r instead" % item)
        self.buttons.append(item)

    def add_button(self, name, url, active=False, disabled=False, extra_classes=None):
        item = Button(name, url,
            active=active,
            disabled=disabled,
            extra_classes=extra_classes
        )
        self.buttons.append(item)
        return item

    def get_context(self):
        return {
            'buttons': self.buttons,
            'extra_classes': self.extra_classes
        }

import abc
from cms.constants import RIGHT, LEFT, REFRESH
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import simplejson


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


class ToolbarAPIMixin(object):
    __metaclass__ = abc.ABCMeta

    def add_item(self, item):
        if not isinstance(item, BaseItem):
            raise ValueError("Items must be subclasses of cms.toolbar.items.BaseItem, %r isn't" % item)
        self.items.append(item)
        return item

    def add_sideframe_item(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=False,
                 on_close=REFRESH, position=LEFT):
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

    def add_modal_item(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=False,
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

    def add_break(self):
        item = Break()
        self.add_item(item)
        return item


class Menu(ToolbarAPIMixin, BaseItem):
    template = "cms/toolbar/menu/list.html"

    def __init__(self, name, csrf_token, url='#', sub_level=False, position=LEFT):
        super(Menu, self).__init__(position)
        self.items = []
        self.menus = {}
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

    def get_context(self):
        return {'items': self.items, 'url': self.url, 'title': self.name, 'sub_level': self.sub_level}


class LinkItem(BaseItem):
    template = "cms/toolbar/menu/link_item.html"

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
    template = "cms/toolbar/menu/sideframe_item.html"

    def __init__(self, name, url, active=False, disabled=False, extra_classes=None, close_on_url_change=True,
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
    template = "cms/toolbar/menu/ajax_item.html"

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
    template = "cms/toolbar/menu/modal_item.html"

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


class DialogItem(BaseItem):
    template = "cms/toolbar/menu/dialog_item.html"



class Break(BaseItem):
    template = "cms/toolbar/menu/break.html"


class Dialog(BaseItem):
    template = "cms/toolbar/menu/dialog.html"

    def __init__(self, url, title, question, right=False):
        super(Dialog, self).__init__(right)
        self.url = url
        self.title = title
        self.question = question

    def __repr__(self):
        return '<Dialog:%s>' % self.title

    def get_context(self):
        return {'url': self.url, 'title': self.title, 'question': self.question}


class ButtonList(BaseItem):
    template = "cms/toolbar/menu/button_list.html"

    def __init__(self, right=False):
        super(ButtonList, self).__init__(right)
        self.items = []

    def addItem(self, name, url, active=False):
        self.items.append({'url': url, 'name': name, 'active': active})

    def get_context(self):
        return {'items': self.items}


class Button(BaseItem):
    template = "cms/toolbar/menu/button.html"


    def get_context(self):
        context = super(Button, self).get_context()
        context['extra_classes'] = self.extra_classes
        return context



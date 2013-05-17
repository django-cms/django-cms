from django.template.loader import render_to_string
from django.utils import simplejson


class BaseItem(object):
    def __init__(self, right=False):
        self.right = right

    def render(self):
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        return {}


class List(BaseItem):
    template = "cms/toolbar/menu/list.html"

    def __init__(self, url, name, sub_level=False, right=False):
        super(List, self).__init__(right)
        self.items = []
        self.url = url
        self.name = name
        self.sub_level = sub_level


    def get_context(self):
        return {'items': self.items, 'url': self.url, 'title': self.name, 'sub_level': self.sub_level}

    def __repr__(self):
        return unicode(self.name)


class Item(BaseItem):
    template = "cms/toolbar/menu/item.html"

    def __init__(self, url, title, load_side_frame=False, ajax=False, ajax_data=None, active=False, question="",
                 right=False, load_modal=True, disabled=False, extra_classes=None):
        super(Item, self).__init__(right)
        if load_side_frame and ajax:
            raise Exception("load_side_frame and ajax can not both be True.")
        self.url = url
        self.load_modal = load_modal
        self.title = title
        self.load_side_frame = load_side_frame
        self.ajax = ajax
        self.active = active
        self.question = question
        self.disabled = disabled
        self.ajax_data = ajax_data
        self.extra_classes = extra_classes

    def get_context(self):
        mod = None
        if self.load_side_frame:
            mod = "sideframe"
        elif self.ajax:
            mod = "ajax"
        elif self.question:
            mod = "dialogue"
        elif self.load_modal:
            mod = "modal"
        data = None
        if self.ajax_data:
            data = simplejson.dumps(self.ajax_data)
        return {
            'url': self.url,
            'title': self.title,
            'type': mod,
            'active': self.active,
            'question': self.question,
            'disabled': self.disabled,
            'data': data,
            'extra_classes': self.extra_classes,
        }

    def __repr__(self):
        return unicode(self.title)


class Break(BaseItem):
    template = "cms/toolbar/menu/break.html"


class Dialog(BaseItem):
    template = "cms/toolbar/menu/dialog.html"

    def __init__(self, url, title, question, right=False):
        super(Dialog, self).__init__(right)
        self.url = url
        self.title = title
        self.question = question

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


class Button(Item):
    template = "cms/toolbar/menu/button.html"


    def get_context(self):
        context = super(Button, self).get_context()
        context['extra_classes'] = self.extra_classes
        return context



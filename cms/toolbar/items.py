from django.template.loader import render_to_string


class BaseItem(object):
    def __init__(self, right=False):
        self.right = right

    def render(self):
        return render_to_string(self.template, self.get_context())

    def get_context(self):
        return {}


class List(BaseItem):
    template = "cms/toolbar/menu/list.html"

    def __init__(self, url, name, right=False):
        super(List, self).__init__(right)
        self.items = []
        self.url = url
        self.name = name


    def get_context(self):
        return {'items': self.items, 'url': self.url, 'title': self.name}

    def __repr__(self):
        return unicode(self.name)


class Item(BaseItem):
    template = "cms/toolbar/menu/item.html"

    def __init__(self, url, title, load_side_frame=False, ajax=False, active=False, question="", right=False,
                 load_modal=True):
        super(Item, self).__init__(right)
        if load_side_frame and ajax:
            raise Exception("laod_side_frame and ajax can not both be True.")
        self.url = url
        self.title = title
        self.load_side_frame = load_side_frame
        self.ajax = ajax
        self.active = active
        self.question = question

    def get_context(self):
        mod = None
        if self.load_side_frame:
            mod = "sideframe"
        elif self.ajax:
            mod = "ajax"
        elif self.question:
            mod = "dialogue"
        return {'url': self.url, 'title': self.title, 'type': mod, 'active': self.active, 'question': self.question}

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


class Switch(BaseItem):
    template = "cms/toolbar/menu/switch.html"

    def __init__(self, right=False):
        super(Switch, self).__init__(right)
        self.items = []

    def addItem(self, name, url, active=False):
        self.items.append({'url': url, 'name': name, 'active': active})

    def get_context(self):
        return {'items': self.items}



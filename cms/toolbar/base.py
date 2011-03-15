# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.middleware.csrf import get_token
from django.template.context import Context
from django.template.loader import render_to_string
from django.utils import simplejson

"""
Possible Interace:


class CMSToolbar(Toolbar):
    items = [
        Switcher('left', 'editmode', 'edit', 'edit-off', 'Edit Mode')
        ...
    ]
"""

class Serializable(object):
    base_attributes = []
    extra_attributes = []
        
    def serialize(self, context, request, **kwargs):
        data = {}
        for python, javascript in self.base_attributes:
            data[javascript] = getattr(self, python)
        for python, javascript in self.extra_attributes:
            data[javascript] = getattr(self, python)
        data.update(self.get_extra_data(context, request, **kwargs))
        return simplejson.dumps(data)
    
    def get_extra_data(self, request, **kwargs):
        return {}


class Toolbar(Serializable):
    def get_items(self, request, **kwargs):
        return []
    
    def get_extra_data(self, request, **kwargs):
        return {
            'debug': settings.TEMPLATE_DEBUG,
            'items': self.get_items(request, **kwargs),
            'csrf_token': get_token(request),
        }


class BaseItem(Serializable):
    base_attributes = [
        ('order', 'order'),
        ('alignment', 'dir'),
        ('item_type', 'type'),
        ('css_class', 'class'),
    ]
    extra_attributes = []
    alignment = 'left'
    
    
    def __init__(self, alignment, css_class_suffix):
        self.alignment = alignment
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
    
    def contribute_to_toolbar(self, toolbar):
        toolbar.items.append(self)
        counter_attr = 'counter_%s' % self.alignment
        current = getattr(toolbar, counter_attr, -1)
        this = current + 1
        self.order = this
        setattr(toolbar, counter_attr, this)
        self.toolbar = toolbar
        

class Switcher(BaseItem):
    item_type = 'switcher'
    
    def __init__(self, alignment, css_class_suffix, add_parameter,
                 remove_parameter, title):
        super(Switcher, self).__init__(alignment, css_class_suffix)
        self.add_parameter = add_parameter
        self.remove_parameter = remove_parameter
        self.title = title
        
    def get_extra_data(self, request, **kwargs):
        state = bool(request.GET.get(self.add_parameter))
        return {
            'state': state
        }


class Anchor(BaseItem):
    """
        {    dir: 'left', type: 'anchor', order: 1, class: 'cms_toolbar-item_logo',
            title: '{% trans "django CMS" %}',
            url: 'http://www.django-cms.org/'
        },
    """
    item_type = 'anchor'
    extra_attributes = [
        ('url', 'url'),
        ('title', 'title'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, url):
        super(Anchor, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.url = url


class HTML(BaseItem):
    item_type = 'html'
    extra_attributes = [
        ('html', 'html'),
    ]
    
    def __init__(self, alignment, css_class_suffix, html):
        super(Anchor, self).__init__(alignment, css_class_suffix)
        self.html = html


class TemplateHTML(BaseItem):
    item_type = 'html'
    
    def __init__(self, alignment, css_class_suffix, template):
        super(Anchor, self).__init__(alignment, css_class_suffix)
        self.template =  template
        
    def get_extra_data(self, request, **kwargs):
        context = Context()
        context['request'] = request
        context.update(kwargs)
        rendered = render_to_string(self.template, context)
        return {
            'html': rendered
        }


class GetButton(BaseItem):
    """
            dir: 'right', type: 'button', order: 50, class: 'cms_toolbar-item_logout',
            title: '{% trans "Logout" %}',
            icon: 'cms_toolbar_icon-lock',
            action: '', hidden: '<input type="hidden" name="logout_submit" />',
            token: "{% csrf_token %}" }
    """
    item_type = 'button'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
        ('action', 'action'),
        ('name', 'name'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, action, name):
        super(GetButton, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.action = action
        self.name = name


class PostButton(BaseItem):
    """
            dir: 'right', type: 'button', order: 50, class: 'cms_toolbar-item_logout',
            title: '{% trans "Logout" %}',
            icon: 'cms_toolbar_icon-lock',
            action: '', hidden: '<input type="hidden" name="logout_submit" />',
            token: "{% csrf_token %}" }
    """
    item_type = 'button'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
        ('action', 'action'),
        ('name', 'name'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, action, name):
        super(PostButton, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.action = action
        self.name = name


class ListItem(object):
    base_attributes = [
        ('title', 'title'),
        ('url', 'url'),
        ('icon', 'icon'),
    ]
    
    def __init__(self, title, url, icon=''):
        self.title = title
        self.url = url
        self.icon = icon


class List(BaseItem):
    """
       { dir: 'right', type: 'list', order: 40, class: 'cms_toolbar-item_admin',
            title: '{% trans "Admin" %}',
            icon: 'cms_toolbar_icon-settings',
            items: [
                { title: '{% trans "Site Administration" %}', url: '{% url admin:index %}', icon: '' }
                {% if has_change_permission %},
                { title: '{% trans "Page Settings" %}', url: '{% url admin:cms_page_change page.pk %}', icon: '' },
                { title: '{% trans "View History" %}', url: '{% url admin:cms_page_history page.pk %}', icon: '' }
                {% endif %}
            ]
        },
    """
    item_type = 'list'
    extra_attributes = [
        ('title', 'title'),
        ('icon', 'icon'),
    ]
    
    def __init__(self, alignment, css_class_suffix, title, icon, items):
        super(List, self).__init__(alignment, css_class_suffix)
        self.title = title
        self.icon = icon
        self.validate_items(items)
        self.raw_items = items
        
    def validate_items(self, items):
        for item in items:
            if not isinstance(item, ListItem):
                raise ImproperlyConfigured(
                    'items of List must be instances of ListItem or a subclass '
                    'of that class.'
                )
    
    def get_extra_data(self, request, **kwargs):
        items = [item.serialize(request, **kwargs) for item in self.raw_items]
        return {
            'items': items
        }
        


"""
    // load css file
    $('<link>').appendTo('head').attr({
        rel: 'stylesheet', type: 'text/css',
        href: '{{ CMS_MEDIA_URL }}css/plugins/cms.toolbar.css'
    });

    // save options
    var options = {
        'placeholder_data': '{{ placeholder_data }}',
        'urls': {
            cms_page_move_plugin: "{% url admin:cms_page_move_plugin %}",
            cms_page_changelist: "{% url admin:cms_page_changelist %}",              
            cms_page_change_template: {% if page %}"{% url admin:cms_page_change_template page.pk %}"{% else %}null{% endif %},
            cms_page_add_plugin: "{% url admin:cms_page_add_plugin %}",
            cms_page_remove_plugin: "{% url admin:cms_page_remove_plugin %}",
            cms_page_move_plugin: "{% url admin:cms_page_move_plugin %}"
        },
        'lang': {
            move_slot: "{% trans 'Move to %(name)s' %}",
            question: "{% trans 'Are you sure you want to delete this plugin?' %}"
        },
        {% if page %}
        'page_is_defined': true
        {% endif %}
    };

    // initialize toolbar and pass all the variables, use same namespace to trigger
    CMS.Toolbar = new CMS.Toolbar('#cms_toolbar-wrapper', options);

    // dummy JSON: {'action_items': [{name: 'edit', icon:'link/zum/zahnrad.jpg', submenu:[{'name': 'Grundeinstellungen', 'action': 'open_url', 'url': 'http:/ksdjagklajsdlkjaskdjf/'}]}]}

    // add logo
    CMS.Toolbar.registerItems([
        {    dir: 'left', type: 'anchor', order: 1, class: 'cms_toolbar-item_logo',
            title: '{% trans "django CMS" %}',
            url: 'http://www.django-cms.org/'
        },
        // when you are logged in
        {% if auth %}
        {    dir: 'left', type: 'switcher', order: 10, class: 'cms_toolbar-item_editmode',
            addParameter: 'edit', removeParameter: 'edit-off',
            state: '{% if edit %}on{% else %}off{% endif %}',
            title: '{% trans "Edit mode" %}',
            url: '/'
        },
        {% if page.last_page_states %}
        {    dir: 'left', type: 'html', order: 20, class: 'cms_toolbar-item_status',
            html: '<div class="cms_toolbar-item"><p>{% trans "Status" %}: <em>{% for state in page.last_page_states %}{{ state.get_action_display }} {% endfor %}</em></p></div>', htmlElement: ''
        },
        {% endif %}
        /*{ dir: 'left', type: 'switcher', order: 20, class: 'cms_toolbar-item_compactmode',
            addParameter: 'compact', removeParameter: 'compact-off',
            state: 'off',
            title: '{% trans "Compact mode" %}',
            url: '/'
        },*/
        { dir: 'right', type: 'button', order: 30, class: 'cms_toolbar-item_page',
            title: '{% trans "Page" %}',
            icon: 'cms_toolbar_icon-edit',
            action: '', hidden: '', token: '',
            redirect: '{% url admin:cms_page_change page.pk %}'
        },
        { dir: 'right', type: 'list', order: 40, class: 'cms_toolbar-item_admin',
            title: '{% trans "Admin" %}',
            icon: 'cms_toolbar_icon-settings',
            items: [
                { title: '{% trans "Site Administration" %}', url: '{% url admin:index %}', icon: '' }
                {% if has_change_permission %},
                { title: '{% trans "Page Settings" %}', url: '{% url admin:cms_page_change page.pk %}', icon: '' },
                { title: '{% trans "View History" %}', url: '{% url admin:cms_page_history page.pk %}', icon: '' }
                {% endif %}
            ]
        },
        {    
            dir: 'right', type: 'button', order: 50, class: 'cms_toolbar-item_logout',
            title: '{% trans "Logout" %}',
            icon: 'cms_toolbar_icon-lock',
            action: '', hidden: '<input type="hidden" name="logout_submit" />',
            token: "{% csrf_token %}" }
        // when you are logged off
        {% else %}
        {    dir: 'left', type: 'html', order: 20, class: 'cms_toolbar-item_login',
            html: '', htmlElement: '#cms_toolbar-item_login'
        },
        { dir: 'right', type: 'button', order: 20, class: 'cms_toolbar-item_admin',
            title: '{% trans "Admin" %}',
            icon: 'cms_toolbar_icon-settings',
            action: '', hidden: '', token: '',
            redirect: '{% url admin:index %}'
        }
        {% endif %}
    ]);
    // or register only one item
    // CMS.Toolbar.registerItem({ item });
});
"""
# -*- coding: utf-8 -*-
from django.utils import simplejson

class BaseItem(object):
    base_attributes = [
        ('order', 'order'),
        ('alignment', 'dir'),
        ('item_type', 'type'),
        ('css_class', 'class'),
    ]
    extra_attributes = []
    alignment = 'left'
    
    def contribute_to_toolbar(self, toolbar):
        toolbar.items.append(self)
        counter_attr = 'counter_%s' % self.alignment
        current = getattr(toolbar, counter_attr, -1)
        this = current + 1
        self.order = this
        setattr(toolbar, counter_attr, this)
        self.toolbar = toolbar
        
    def serialize(self, request, **kwargs):
        data = {}
        for python, javascript in self.base_attributes:
            data[javascript] = getattr(self, python)
        for python, javascript in self.extra_attributes:
            data[javascript] = getattr(self, python)
        data.update(self.get_extra_data(request, **kwargs))
        return simplejson.dumps(data)
    
    def get_extra_data(self, request, **kwargs):
        return {}


class Switcher(BaseItem):
    item_type = 'switcher'
    
    extra_attributes = [
        ('url', 'url'),
    ]
    
    def __init__(self, alignment, css_class_suffix, add_parameter,
                 remove_parameter, title, url='/'):
        self.url = url
        self.alignment = alignment
        self.css_class_suffix = css_class_suffix
        self.css_class = 'cms_toolbar-item_%s' % self.css_class_suffix
        self.add_parameter = add_parameter
        self.remove_parameter = remove_parameter
        
    def get_extra_data(self, request, **kwargs):
        state = bool(request.GET.get(self.add_parameter))
        return {'state': state}


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
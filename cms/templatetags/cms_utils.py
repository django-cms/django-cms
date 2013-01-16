from classytags.arguments import Argument
from classytags.core import Tag, Options
from classytags.helpers import InclusionTag
from django import template
from django.template.defaultfilters import safe
from cms.models import Page
from cms.plugins.snippet.models import Snippet
from cms.plugins.snippet.cms_plugins import SnippetPlugin
from builder.views import BuilderListView
import settings

register = template.Library()

def snippet_html(context, name):
    """
    Render snippent with given name
    """
    content = context.get('content')
    new_content = ''

    try:
        s = Snippet.objects.get(name=name)
        t = SnippetPlugin(s)

        class fake_instant(object):
            snippet = ''

        i = fake_instant()
        i.snippet = s
        new_content = t.render(context, i, '').get('content')
    except Exception, e:
        new_content = str(e)

    # restore content
    context['content'] = content

    return new_content
register.simple_tag(takes_context=True)(snippet_html)

def loadpage(context, reverse_id):
    """
    Loaded page with current reverse_id
    """
    page = Page.objects.get(reverse_id=reverse_id)
    context.__setattr__(reverse_id, page)
    return ''
register.simple_tag(takes_context=True)(loadpage)


class PageList(BuilderListView):
    model = Page
    paginate_by = getattr(settings, 'PAGINATION_DEFAULT_PAGINATION', 12)
    template_name = 'cms/snippet/list.html'

    def get_queryset(self):
        return Page.objects.filter(parent=self.kwargs['parent_page'], published=True).order_by('-creation_date')[:self.kwargs['limit']] # .with_user(context['user']).filter(can_read_permissions=True)



class GetChilderns(InclusionTag):
    name = 'get_childrens'
    template = 'cms/snippet/list.html'
    options = Options(
        Argument('page', default=None, required=False),
        Argument('template', default=None, required=False),
        Argument('imgsize', default=None, required=False),
        Argument('limit', default=4, required=False),
        'as',
        Argument('varname', resolve=False, default='childrens', required=False),
    )

    def get_value(self, context):
        return 'dummy'

    def get_context(self, context, page, template, imgsize, limit, varname):
        if page is None:
            page = context['request'].current_page
        elif isinstance(page, basestring):
            page = Page.objects.get(reverse_id = page)


        if template:
            self.template = template

        if imgsize is None:
            imgsize = settings.CMS_PAGE_IMGSIZE
        context['imgsize'] = imgsize

        if varname == 'childrens':
            context['as_empty'] = True
        else:
            context['as_empty'] = False

        pl = PageList(**{'request' : context['request']})
        pl.template_name = self.template
        pl.kwargs = context['request'].GET.copy()
        pl.kwargs['limit'] = limit
        pl.kwargs['parent_page'] = page
        objects = pl.get(request = context['request']).context_data
        context[varname] = objects['object_list']
        context['object_list'] = objects['object_list']
        context['paginator'] = objects['paginator']
        context['page_obj'] = objects['page_obj']
        context['is_paginated'] = objects['is_paginated']

        return context

register.tag(GetChilderns)

class GetSubChilderns(InclusionTag):
    name = 'get_subchildrens'
    template = 'cms/snippet/list.html'
    options = Options(
        Argument('page', default=None, required=False),
        Argument('template', default=None, required=False),
        Argument('imgsize', default=None, required=False),
        Argument('limit', default=4, required=False),
        'as',
        Argument('varname', resolve=False, default='childrens', required=False),
    )

    def get_value(self, context):
        return 'dummy'

    def get_context(self, context, page, template, imgsize, limit, varname):
        if page is None:
            page = context['request'].current_page
        elif isinstance(page, basestring):
            page = Page.objects.get(reverse_id=page)

        if template:
            self.template = template

        if imgsize is None:
            imgsize = settings.CMS_PAGE_IMGSIZE
        context['imgsize'] = imgsize

        if varname == 'childrens':
            context['as_empty'] = True
        else:
            context['as_empty'] = False

        # ToDo
        # Fix problems with permission
        context[varname] = Page.objects.filter(parent__parent=page, published=True).order_by('-creation_date')[:limit] # .with_user(context['user']).filter(can_read_permissions=True)
        return context

register.tag(GetSubChilderns)


class control_data(Tag):
    """
        {% control_data cms.Page filter='parent=5,is_published=1' order='-id' as childrens %}
    """
    name = 'control_data'
    options = Options(
        Argument('object'),
        Argument('filtr', required=False, default=None),
        Argument('order', required=False, default=None),
        'as',
        Argument('varname', required=False, resolve=False)
    )

    def render_tag(self, context, object, filtr, order, varname):
        from django.db.models import Q
        model = __import__(object.split('.')[0]).models.__dict__.get(object.split('.')[1])
        object_list = model.objects.filter()

        if filtr:
            q = Q()
            for exp in filtr.split(','):
                v = exp.split('=')

                if v[1].startswith('{{ '):
                    v[1] = context[v[1].replace('{{ ','').replace(' }}', '')]

                try:
                    q &= Q(**{ v[0] : v[1] })
                except IndexError:
                    pass

            object_list = object_list.filter(q)
        if order:
            object_list.order_by(order)

        if varname:
            context[varname] = object_list
            return ''
        else:
            return object_list

register.tag(control_data)

def get_plugin_content(context, plugin_name, page, slot, plugin_type):
    """
     Return plugin of giving page and slot
    """
    try:
        context[plugin_name] = page.placeholders.filter(slot = slot)[0].cmsplugin_set.filter(plugin_type = plugin_type)
    except :
        pass
    return ''
register.simple_tag(takes_context=True)(get_plugin_content)


def standart_form(form, save_button = 'Save', cancel_button = None):
    return {'form' : form, 'save_button' : save_button, 'cancel_button' : cancel_button}
register.inclusion_tag('snippet/standart_form.html')(standart_form)

def get_contact_form(context, data = False):
    from contact_form.forms import ContactForm
    c = ContactForm(request=context['request'])
    context['contact_form'] = c
    return ''
register.simple_tag(takes_context=True)(get_contact_form)

def klass(ob):
    return ob.__class__.__name__
register.filter('klass')(klass)
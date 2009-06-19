from django.conf import settings
from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.sites.models import Site
from cms import settings as cms_settings
from cms.models import MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS
from cms.utils.admin import get_admin_menu_item_context
from cms.utils import get_language_from_request

register = template.Library()

def show_admin_menu(context, page):# , no_children=False):
    """Render the admin table of pages"""
    request = context['request']
    
    if context.has_key("cl"):
        filtered = context['cl'].is_filtered()
    elif context.has_key('filtered'):
        filtered = context['filtered']
    
    # following function is newly used for getting the context per item (line)
    # if something more will be required, then get_admin_menu_item_context
    # function have to be updated. 
    # This is done because item can be reloaded after some action over ajax.
    context.update(get_admin_menu_item_context(request, page, filtered))
    
    # this here is just context specific for menu rendering - items itself does
    # not use any of following variables
    #context.update({
    #    'no_children': no_children,
    #})
    return context
show_admin_menu = register.inclusion_tag('admin/cms/page/menu.html',
                                         takes_context=True)(show_admin_menu)


def clean_admin_list_filter(cl, spec):
    """
    used in admin to display only these users that have actually edited a page and not everybody
    """
    choices = sorted(list(spec.choices(cl)), key=lambda k: k['query_string'])
    query_string = None
    unique_choices = []
    for choice in choices:
        if choice['query_string'] != query_string:
            unique_choices.append(choice)
            query_string = choice['query_string']
    return {'title': spec.title(), 'choices' : unique_choices}
clean_admin_list_filter = register.inclusion_tag('admin/filter.html')(clean_admin_list_filter)



@register.filter
def boolean_icon(value):
    BOOLEAN_MAPPING = {True: 'yes', False: 'no', None: 'unknown'}
    return mark_safe(u'<img src="%simg/admin/icon-%s.gif" alt="%s" />' % (settings.ADMIN_MEDIA_PREFIX, BOOLEAN_MAPPING[value], value))

@register.filter
def moderator_choices(page, user):    
    """Returns simple moderator choices used for checkbox rendering, as a value
    is used mask value.
    """
    try:
        page_moderator = page.pagemoderator_set.get(user=user)
    except ObjectDoesNotExist:
        page_moderator = None
    
    moderate = (
        ('moderate_page', _('Moderate page'), _('Unbind page moderation'), MASK_PAGE), 
        ('moderate_children', _('Moderate children'), _('Unbind children moderation'), MASK_CHILDREN),
        ('moderate_descendants', _('Moderate descendants'), _('Unbind descendants moderation'), MASK_DESCENDANTS),
    )
        
    for name, title_yes, title_no, value in moderate:
        active = page_moderator and getattr(page_moderator, name)
        title = active and title_no or title_yes
        yield value, title, active, name.split('_')[1]
        
def do_page_admin_language(parser, token):
    error_string = u'%r tag requires one argument' % token.split_contents()[0]
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(bits) >= 2:
        #tag_name, page
        return PageAdminLanguageNode(bits[1])
    else:
        raise template.TemplateSyntaxError(error_string)

class PageAdminLanguageNode(template.Node):
    """This template node is used to output GET attribute for selected editing language in admin
    when entering Page Edit view.
    
    eg: {% page_admin_language page %}
    
    Keyword arguments:
    page -- the page for which the language GET should be rendered.
    """
    def __init__(self, page):
        self.page = template.Variable(page)

    def render(self, context):
        if not 'request' in context:
            return ''
        try:
            lang = get_language_from_request(context['request'])
            page = self.page.resolve(context)
            page_languages = page.get_languages()
            if lang not in page_languages and len(page_languages):
                return page_languages[0]
            else:
                return lang
        except template.VariableDoesNotExist:
            return ''
        
    def __repr__(self):
        return "<PageAdminLanguage Node: %s>" % self.page

register.tag('page_admin_language', do_page_admin_language)

from django.conf import settings
from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from cms.models import MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS
from cms.utils.admin import get_admin_menu_item_context

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
    is used mask value. Optimized, uses caching from change list.
    """
    moderation_value = page.get_moderation_value(user)
    
    moderate = (
        (MASK_PAGE, _('Moderate page'), _('Unbind page moderation'), 'page'), 
        (MASK_CHILDREN, _('Moderate children'), _('Unbind children moderation'), 'children'),
        (MASK_DESCENDANTS, _('Moderate descendants'), _('Unbind descendants moderation'), 'descendants'),
    )
    
    choices = []
    for mask_value, title_yes, title_no, kind in moderate:
        active = moderation_value and moderation_value & mask_value
        title = active and title_no or title_yes
        choices.append((mask_value, title, active, kind))
    
    return choices

@register.filter
def preview_link(page, language):
    if 'cms.middleware.multilingual.MultilingualURLMiddleware' in settings.MIDDLEWARE_CLASSES:
        from django.core.urlresolvers import reverse

        # Which one of page.get_slug() and page.get_path() is the right
        # one to use in this block? They both seem to return the same thing.
        try:
            # attempt to retrieve the localized path/slug and return
            root = reverse('pages-root')
            return root + language + "/" + page.get_absolute_url(language, fallback=False)[len(root):]
        except:
            # no localized path/slug. therefore nothing to preview. stay on the same page.
            # perhaps the user should be somehow notified for this.
            return ''
    return page.get_absolute_url(language)

def render_plugin(context, plugin):
    return {'content': plugin.render_plugin(context, admin=True)}

render_plugin = register.inclusion_tag('cms/content.html', takes_context=True)(render_plugin)

def page_submit_row(context):
    opts = context['opts']
    change = context['change']
    is_popup = context['is_popup']
    save_as = context['save_as']
    show_delete_translation = context.get('show_delete_translation')  
    language = context['language']
    return {
        'onclick_attrib': (opts.get_ordered_objects() and change
                            and 'onclick="submitOrderForm();"' or ''),
        'show_delete_link': (not is_popup and context['has_delete_permission']
                              and (change or context['show_delete'])),
        'show_save_as_new': not is_popup and change and save_as,
        'show_save_and_add_another': context['has_add_permission'] and 
                            not is_popup and (not save_as or context['add']),
        'show_save_and_continue': not is_popup and context['has_change_permission'],
        'is_popup': is_popup,
        'show_save': True,
        'language': language,
        'language_name': [name for langcode, name in settings.CMS_LANGUAGES if langcode == language][0],
        'show_delete_translation': show_delete_translation
    }
page_submit_row = register.inclusion_tag('admin/page_submit_line.html', takes_context=True)(page_submit_row)

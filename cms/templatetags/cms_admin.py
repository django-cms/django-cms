from django.conf import settings
from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from cms.models import MASK_PAGE, MASK_CHILDREN, MASK_DESCENDANTS

register = template.Library()

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
        ('moderate_page', _('Moderate page'), MASK_PAGE), 
        ('moderate_children', _('Moderate children'), MASK_CHILDREN),
        ('moderate_descendants', _('Moderate descendants'), MASK_DESCENDANTS),
    )
        
    for name, title, value in moderate:
        active = page_moderator and getattr(page_moderator, name)
        yield value, title, active
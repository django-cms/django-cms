from os.path import join
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.forms.widgets import Widget, Select
from cms.models import PageUser


class PluginEditor(Widget):
    def __init__(self, attrs=None, installed=None, list=None):
        if attrs is not None:
            self.attrs = attrs.copy()
        else:
            self.attrs = {}
        
    class Media:
        js = [join(settings.CMS_MEDIA_URL, path) for path in (
            'js/lib/ui.core.js',
            'js/lib/ui.sortable.js',
            'js/plugin_editor.js',
        )]
        css = {
            'all': [join(settings.CMS_MEDIA_URL, path) for path in (
                'css/plugin_editor.css',
            )]
        }

    def render(self, name, value, attrs=None):
        
        context = {
            'plugin_list': self.attrs['list'],
            'installed_plugins': self.attrs['installed'],
            'traduction_language': self.attrs['traduction_language'],
            'language': self.attrs['language'],
            'show_language_tabs': len(settings.CMS_LANGUAGES) > 1 and \
                not settings.CMS_DBGETTEXT,
        }
        return mark_safe(render_to_string(
            'admin/cms/page/widgets/plugin_editor.html', context))


class UserSelectAdminWidget(Select):
    """Special widget used in page permission inlines, because we have to render
    an add user (plus) icon, but point it somewhere else - to special user creation
    view, which is accessible only if user haves "add user" permissions.
    
    Current user should be assigned to widget in form constructor as an user 
    attribute.
    """
    def render(self, name, value, attrs=None, choices=()):
        output = [super(UserSelectAdminWidget, self).render(name, value, attrs, choices)]    
        if hasattr(self, 'user') and (self.user.is_superuser or \
            self.user.has_perm(PageUser._meta.app_label + '.' + PageUser._meta.get_add_permission())):
            # append + icon
            add_url = '../../../cms/pageuser/add/'
            output.append(u'<a href="%s" class="add-another" id="add_id_%s" onclick="return showAddAnotherPopup(this);"> ' % \
                    (add_url, name))
            output.append(u'<img src="%simg/admin/icon_addlink.gif" width="10" height="10" alt="%s"/></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Add Another')))
        return mark_safe(u''.join(output))

    

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.forms.widgets import Media
import operator 


class Placeholder(models.Model):
    slot = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    default_width = models.PositiveSmallIntegerField(_("width"), null=True, editable=False)
    
    def __unicode__(self):
        return self.slot
        
    class Meta:
        app_label = 'cms'

    def has_change_permission(self, request):
        opts = self._meta
        if request.user.is_superuser:
            return True
        return request.user.has_perm(opts.app_label + '.' + opts.get_change_permission())
    
    def render(self, context, width):
        from cms.utils.plugin import render_plugins_for_context
        if not 'request' in context:
            return '<!-- missing request -->'
        return render_plugins_for_context(self, context, width or self.default_width)
    
    def get_media(self, request, context):
        from cms.plugins.utils import get_plugin_media
        media_classes = [get_plugin_media(request, context, plugin) for plugin in self.cmsplugin_set.all()]
        if media_classes:
            return reduce(operator.add, media_classes)
        return Media()
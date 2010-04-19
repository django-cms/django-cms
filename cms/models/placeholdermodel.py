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
        from cms.plugin_rendering import render_placeholder
        if not 'request' in context:
            return '<!-- missing request -->'
        context.update({'width': width or self.default_width})
        return render_placeholder(self, context)

    def get_media(self, request, context):
        from cms.plugins.utils import get_plugin_media
        media_classes = [get_plugin_media(request, context, plugin) for plugin in self.cmsplugin_set.all()]
        if media_classes:
            return reduce(operator.add, media_classes)
        return Media()
    
    def _get_attached_models(self):
        from cms.models import CMSPlugin
        for rel in self._meta.get_all_related_objects():
            if isinstance(rel.model, CMSPlugin):
                continue
            field = getattr(self, rel.get_accessor_name())
            if field.count():
                return [(f, rel.field) for f in field.all()]
        return []
    
    def generic_copy(self, target_language):
        plugins = list(self.cmsplugin_set.all().order_by('tree_id', '-rght'))
        results = []
        for model, field in self._get_attached_models():
            func = getattr(field, 'copy_function', None)
            if func:
                success = func(placeholder=self, target_language=target_language,
                    fieldname=field.name, model=model, plugins=plugins)
                results.append(success)
            else:
                results.append(False)
        if all(results):
            return plugins
        return False
    
    def get_copy_languages(self):
        languages = set()
        for model, field in self._get_attached_models():
            func = getattr(field, 'get_copy_languages', None)
            if func and callable(func):
                languages.update(func(placeholder=self, model=model, fieldname=field.name))
        return sorted(languages)
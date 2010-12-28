from cms.utils.helpers import reversion_register
from cms.utils.placeholder import PlaceholderNoAction
from django.db import models
from django.forms.widgets import Media
from django.utils.translation import ugettext_lazy as _
import operator


class PlaceholderManager(models.Manager):
    def _orphans(self):
        """
        Private method because it should never actually return anything.
        """
        from cms.models import CMSPlugin
        m2m = self.model._meta.get_all_related_many_to_many_objects()
        fks = self.model._meta.get_all_related_objects()
        kwargs = {}
        for rel in m2m:
            kwargs[rel.var_name] = None
        for rel in fks:
            if rel.model == CMSPlugin:
                continue
            kwargs[rel.var_name] = None
        return self.filter(**kwargs)
 

class Placeholder(models.Model):
    slot = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    default_width = models.PositiveSmallIntegerField(_("width"), null=True, editable=False)

    objects = PlaceholderManager()

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
    
    def _get_attached_field(self):
        from cms.models import CMSPlugin
        if not hasattr(self, '_attached_field_cache'):
            self._attached_field_cache = None
            for rel in self._meta.get_all_related_objects():
                if isinstance(rel.model, CMSPlugin):
                    continue
                field = getattr(self, rel.get_accessor_name())
                if field.count():
                    self._attached_field_cache = rel.field
        return self._attached_field_cache
    
    def _get_attached_field_name(self):
        field = self._get_attached_field()
        if field:
            return field.name
        return None
    
    def _get_attached_model(self):
        field = self._get_attached_field()
        if field:
            return field.model
        return None

    def get_plugins_list(self):
        return list(self.get_plugins())
    
    def get_plugins(self):
        return self.cmsplugin_set.all().order_by('tree_id', '-rght')
    
    @property
    def actions(self):
        if not hasattr(self, '_actions_cache'):
            field = self._get_attached_field()
            self._actions_cache = getattr(field, 'actions', PlaceholderNoAction())
        return self._actions_cache

reversion_register(Placeholder) # follow=["cmsplugin_set"] not following plugins since they are a spechial case
# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe

def plugin_meta_context_processor(instance, placeholder):
    return {
        'plugin_index': instance._render_meta.index, # deprecated template variable
        'plugin': {
            'counter': instance._render_meta.index + 1,
            'counter0': instance._render_meta.index,
            'revcounter': instance._render_meta.total - instance._render_meta.index,
            'revcounter0': instance._render_meta.total - instance._render_meta.index - 1,
            'first': instance._render_meta.index == 0,
            'last': instance._render_meta.index == instance._render_meta.total - 1,
            'total': instance._render_meta.total,
            'id_attr': 'plugin_%i_%i' % (instance.placeholder_id, instance.pk),
            'instance': instance,
        }
    }

def mark_safe_plugin_processor(instance, placeholder, rendered_content, original_context):
    return mark_safe(rendered_content)
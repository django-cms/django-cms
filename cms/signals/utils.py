from contextlib import contextmanager

from django.db.models import signals

from ..models.pluginmodel import CMSPlugin
from .plugins import (
    pre_delete_plugins,
    pre_save_plugins,
    post_delete_plugins,
)


@contextmanager
def disable_cms_plugin_signals():
    """
    Disconnects all plugin signal handlers registered in the core.
    """
    plugin_signals = (
        (signals.pre_delete, pre_delete_plugins, 'cms_pre_delete_plugin'),
        (signals.pre_save, pre_save_plugins, 'cms_pre_save_plugin'),
        (signals.post_delete, post_delete_plugins, 'cms_post_delete_plugin'),
    )

    from cms.plugin_pool import plugin_pool

    plugins = plugin_pool.registered_plugins

    for signal, handler, dispatch_id in plugin_signals:
        signal.disconnect(
            handler,
            sender=CMSPlugin,
            dispatch_uid=dispatch_id,
        )

    for plugin in plugins:
        for signal, handler, dispatch_id in plugin_signals:
            signal.disconnect(
                handler,
                sender=plugin.model,
                dispatch_uid=dispatch_id + '_%s' % plugin.value,
            )

    yield

    for signal, handler, dispatch_id in plugin_signals:
        signal.connect(
            handler,
            sender=CMSPlugin,
            dispatch_uid=dispatch_id,
        )

    for plugin in plugins:
        for signal, handler, dispatch_id in plugin_signals:
            signal.connect(
                handler,
                sender=plugin.model,
                dispatch_uid=dispatch_id + '_%s' % plugin.value
            )


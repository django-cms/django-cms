# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import get_object_or_404

from cms.models import Page, Title, CMSPlugin, Placeholder


def revert_plugins(request, version_id, obj):
    from cms.utils.reversion_hacks import Version

    version = get_object_or_404(Version, pk=version_id)
    revs = [related_version.object_version for related_version in version.revision.version_set.all()]
    cms_plugin_list = []
    placeholders = {}
    plugin_list = []
    titles = []
    others = []
    page = obj
    for rev in revs:
        obj = rev.object
        if obj.__class__ == Placeholder:
            placeholders[obj.pk] = obj
        if obj.__class__ == CMSPlugin:
            cms_plugin_list.append(obj)
        elif hasattr(obj, 'cmsplugin_ptr_id'):
            plugin_list.append(obj)
        elif obj.__class__ == Page:
            pass
        elif obj.__class__ == Title:
            titles.append(obj)
        else:
            others.append(rev)
    if not page.has_change_permission(request):
        raise Http404
    current_plugins = list(CMSPlugin.objects.filter(placeholder__page=page))
    for pk, placeholder in placeholders.items():
        # admin has already created the placeholders/ get them instead
        try:
            placeholders[pk] = page.placeholders.get(slot=placeholder.slot)
        except Placeholder.DoesNotExist:
            placeholders[pk].save()
            page.placeholders.add(placeholders[pk])
    for plugin in cms_plugin_list:
        # connect plugins to the correct placeholder
        plugin.placeholder = placeholders[plugin.placeholder_id]
        plugin.save(no_signals=True)
    for plugin in cms_plugin_list:
        plugin.save()
        for p in plugin_list:
            if int(p.cmsplugin_ptr_id) == int(plugin.pk):
                plugin.set_base_attr(p)
                p.save()
        for old in current_plugins:
            if old.pk == plugin.pk:
                plugin.save()
                current_plugins.remove(old)
    for title in titles:
        title.page = page
        try:
            title.save()
        except:
            title.pk = Title.objects.get(page=page, language=title.language).pk
            title.save()
    for other in others:
        other.object.save()
    for plugin in current_plugins:
        plugin.delete()

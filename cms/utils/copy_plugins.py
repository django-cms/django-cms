# -*- coding: utf-8 -*-
def copy_plugins_to(plugin_list, to_placeholder, to_language = None):
    """
    Copies a list of plugins to a placeholder to a language.
    """
    ptree = []
    plugins_ziplist = []
    for old_plugin in plugin_list:
        if to_language:
            plugin_language = to_language
        else:
            plugin_language = old_plugin.language
        # do the simple copying
        new_plugin = old_plugin.copy_plugin(to_placeholder, plugin_language, ptree)
        plugins_ziplist.append((new_plugin, old_plugin))
    # this magic is needed for advanced plugins like Text Plugins that can have
    # nested plugins and need to update their content based on the new plugins.
    for new_plugin, old_plugin in plugins_ziplist:
        new_instance = new_plugin.get_plugin_instance()[0]
        if new_instance:
            new_instance.post_copy(old_plugin, plugins_ziplist)
    # returns information about originals and copies
    return plugins_ziplist

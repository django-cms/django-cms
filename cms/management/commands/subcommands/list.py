# -*- coding: utf-8 -*-
from cms.management.commands.subcommands.base import SubcommandsCommand
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title
from django.core.management.base import NoArgsCommand


class ListApphooksCommand(NoArgsCommand):
    
    help = 'Lists all apphooks in pages'
    def handle_noargs(self, **options):
        urls = Title.objects.filter(application_urls__gt='').values_list("application_urls", flat=True)
        for url in urls:
            self.stdout.write('%s\n' % url)
            
class ListPluginsCommand(NoArgsCommand):

    help = 'Lists all plugins in CMSPlugin'
    def handle_noargs(self, **options):
        plugins = CMSPlugin.objects.distinct().values_list("plugin_type", flat=True)
        for plugin in plugins:
            self.stdout.write(plugin+'\n')            
    
class ListCommand(SubcommandsCommand):
    help = 'List commands'
    subcommands = {
        'apphooks': ListApphooksCommand,
        'plugins': ListPluginsCommand
    }
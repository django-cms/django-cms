from optparse import make_option
from django.core.management.base import BaseCommand, LabelCommand, CommandError
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title

class SubcommandsCommand(BaseCommand):

    def __init__(self):
        super(SubcommandsCommand, self).__init__()
        extra_options = []
        for subcommand, command in self.subcommands.items():
            extra_options.append(
                make_option('--%s' % subcommand,
                    action='store_true',
                    dest=subcommand,
                    default=False,
                    help=command.help)
                )
            for option in command.option_list:
                extra_options.append(option)
                
        self.option_list = BaseCommand.option_list + tuple(extra_options)

    def handle(self, *args, **options):
 
        handle_command = None 
        for subcommand, command in self.subcommands.items():
            if options[subcommand] == True:
                handle_command = command()
                del options[subcommand]
                
        if handle_command:
            handle_command.execute(*args, **options)
        else:
            raise CommandError('No cms command in options')
            
class UninstallApphooksCommand(LabelCommand):
    
    option_list = tuple()
    args = "APPHOK_NAME"
    label = 'apphook name (SampleApp)'
    help = 'Uninstalls (sets to null) specified apphooks for all pages'
    
    def handle_label(self, label, **options):
        queryset = Title.objects.filter(application_urls=label)
        number_of_apphooks = queryset.count()
        
        if number_of_apphooks > 0:
            queryset.update(application_urls=None)
            self.stdout.write('%d "%s" apphooks uninstalled' % (number_of_apphooks, label))
        else:
            self.stdout.write('no "%s" apphooks found' % label)
            
class UninstallPluginsCommand(LabelCommand):
    
    option_list = tuple()
    args = "PLUGIN_NAME"
    label = 'plugin name (SamplePlugin)'
    help = 'Uninstalls (deletes) specified plugins from the CMSPlugin model'
    
    def handle_label(self, label, **options):
        queryset = CMSPlugin.objects.filter(type=label)
        number_of_plugins = queryset.count()
        
        if number_of_apphooks > 0:
            queryset.delete()
            self.stdout.write('%d "%s" plugins uninstalled' % (number_of_plugins, label))
        else:
            self.stdout.write('no "%s" plugins found' % label)            
            
class Command(SubcommandsCommand):
    subcommands = {
        'uninstall_apphooks': UninstallApphooksCommand,
        'uninstall_plugins': UninstallPluginsCommand
    }
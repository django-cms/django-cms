from optparse import make_option
from django.core.management.base import BaseCommand, LabelCommand, CommandError

class SubcommandsCommand(BaseCommand):

    def handle(self, *args, **options):
        if len(args) > 0:
            if args[0] in self.subcommands.keys():
                handle_command = self.subcommands.get(args[0])()
            else:
                raise CommandError('No such command "%s"' % args[0])        
            if handle_command:
                handle_command.execute(*args[1:], **options)
        else:
            raise CommandError('No commands in arguments')
            
class UninstallApphooksCommand(LabelCommand):
    
    args = "APPHOK_NAME"
    label = 'apphook name (SampleApp)'
    help = 'Uninstalls (sets to null) specified apphooks for all pages'
    
    def handle_label(self, label, **options):
        from cms.models.titlemodels import Title
        queryset = Title.objects.filter(application_urls=label)
        number_of_apphooks = queryset.count()
        
        if number_of_apphooks > 0:
            queryset.update(application_urls=None)
            self.stdout.write('%d "%s" apphooks uninstalled' % (number_of_apphooks, label))
        else:
            self.stdout.write('no "%s" apphooks found' % label)
            
class UninstallPluginsCommand(LabelCommand):

    args = "PLUGIN_NAME"
    label = 'plugin name (SamplePlugin)'
    help = 'Uninstalls (deletes) specified plugins from the CMSPlugin model'
    
    def handle_label(self, label, **options):
        from cms.models.pluginmodel import CMSPlugin
        queryset = CMSPlugin.objects.filter(type=label)
        number_of_plugins = queryset.count()
        
        if number_of_apphooks > 0:
            queryset.delete()
            self.stdout.write('%d "%s" plugins uninstalled' % (number_of_plugins, label))
        else:
            self.stdout.write('no "%s" plugins found' % label)            

class UninstallCommand(SubcommandsCommand):
    help = 'Uninstall commands'
    subcommands = {
        'apphooks': UninstallApphooksCommand,
        'plugins': UninstallPluginsCommand
    }

class Command(SubcommandsCommand):
    help = 'Various django-cms commands'
    subcommands = {
        'uninstall': UninstallCommand,
    }
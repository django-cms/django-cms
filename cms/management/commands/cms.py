# -*- coding: utf-8 -*-
from __future__ import absolute_import
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, NoArgsCommand, LabelCommand, CommandError
from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title

class SubcommandsCommand(BaseCommand):
    subcommands = {}
    command_name = ''

    def __init__(self):
        super(SubcommandsCommand, self).__init__()
        for name, subcommand in self.subcommands.items():
            subcommand.command_name = '%s %s' % (self.command_name, name)

    def handle(self, *args, **options):
        stderr = getattr(self, 'stderr', sys.stderr)
        stdout = getattr(self, 'stdout', sys.stdout)
        if len(args) > 0:
            if args[0] in self.subcommands.keys():
                handle_command = self.subcommands.get(args[0])()
                handle_command.stdout = stdout
                handle_command.stderr = stderr
                handle_command.handle(*args[1:], **options)
            else:
                stderr.write("%r is not a valid subcommand for %r\n" % (args[0], self.command_name))
                stderr.write("Available subcommands are:\n")
                for subcommand in sorted(self.subcommands.keys()):
                    stderr.write("  %r\n" % subcommand)
                raise CommandError('Invalid subcommand %r for %r' % (args[0], self.command_name))
        else:
            stderr.write("%r must be called with at least one argument, it's subcommand.\n" % self.command_name)
            stderr.write("Available subcommands are:\n")
            for subcommand in sorted(self.subcommands.keys()):
                stderr.write("  %r\n" % subcommand)
            raise CommandError('No subcommand given for %r' % self.command_name)
            
class UninstallApphooksCommand(LabelCommand):
    
    args = "APPHOK_NAME"
    label = 'apphook name (eg SampleApp)'
    help = 'Uninstalls (sets to null) specified apphooks for all pages'
    
    def handle_label(self, label, **options):
        queryset = Title.objects.filter(application_urls=label)
        number_of_apphooks = queryset.count()

        if number_of_apphooks > 0:
            if options.get('interactive'):
                confirm = raw_input("""
You have requested to remove %d %r apphooks.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (number_of_apphooks, label))
            else:
                confirm = 'yes'
            if confirm == 'yes':
                queryset.update(application_urls=None)
                self.stdout.write('%d %r apphooks uninstalled\n' % (number_of_apphooks, label))
        else:
            self.stdout.write('no %r apphooks found\n' % label)
            
class UninstallPluginsCommand(LabelCommand):

    args = "PLUGIN_NAME"
    label = 'plugin name (eg SamplePlugin)'
    help = 'Uninstalls (deletes) specified plugins from the CMSPlugin model'
    
    def handle_label(self, label, **options):
        queryset = CMSPlugin.objects.filter(plugin_type=label)
        number_of_plugins = queryset.count()
        
        if number_of_plugins > 0:
            if options.get('interactive'):
                confirm = raw_input("""
You have requested to remove %d %r plugins.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (number_of_plugins, label))
            else:
                confirm = 'yes'
            queryset.delete()
            self.stdout.write('%d %r plugins uninstalled\n' % (number_of_plugins, label))
        else:
            self.stdout.write('no %r plugins found\n' % label)            

class UninstallCommand(SubcommandsCommand):
    help = 'Uninstall commands'
    subcommands = {
        'apphooks': UninstallApphooksCommand,
        'plugins': UninstallPluginsCommand
    }
    
class ListApphooksCommand(NoArgsCommand):
    
    help = 'Lists all apphooks in pages'
    def handle_noargs(self, **options):
        urls = Title.objects.values_list("application_urls", flat=True)
        for url in urls:
            self.stdout.write(url+'\n')
            
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
    
class Command(SubcommandsCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
        help='Tells django-cms to NOT prompt the user for input of any kind. '),
    )

    command_name = 'cms'
    
    help = 'Various django-cms commands'
    subcommands = {
        'uninstall': UninstallCommand,
        'list': ListCommand,
    }
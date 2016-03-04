# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import LabelCommand
from django.utils.six.moves import input

from cms.models import Page
from cms.models.pluginmodel import CMSPlugin
from cms.plugin_pool import plugin_pool

from .base import SubcommandsCommand


class UninstallApphooksCommand(LabelCommand):
    args = 'APPHOK_NAME'
    command_name = 'apphooks'
    label = 'apphook name (eg SampleApp)'
    help_string = 'Uninstalls (sets to null) specified apphooks for all pages'

    def handle_label(self, label, **options):
        queryset = Page.objects.filter(application_urls=label)
        number_of_apphooks = queryset.count()

        if number_of_apphooks > 0:
            if options.get('interactive'):
                confirm = input("""
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
    args = 'PLUGIN_NAME'
    command_name = 'plugins'
    label = 'plugin name (eg SamplePlugin)'
    help_string = 'Uninstalls (deletes) specified plugins from the CMSPlugin model'
    missing_args_message = 'foo bar'

    def handle_label(self, label, **options):
        plugin_pool.get_all_plugins()
        queryset = CMSPlugin.objects.filter(plugin_type=label)
        number_of_plugins = queryset.count()

        if number_of_plugins > 0:
            if options.get('interactive'):
                confirm = input("""
You have requested to remove %d %r plugins.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (number_of_plugins, label))
            else:
                confirm = 'yes'
            if confirm == 'yes':
                queryset.delete()
                self.stdout.write('%d %r plugins uninstalled\n' % (number_of_plugins, label))
            else:
                self.stdout.write('Aborted')
        else:
            self.stdout.write('no %r plugins found\n' % label)


class UninstallCommand(SubcommandsCommand):
    help_string = 'Uninstall objects instances of the following types:'
    command_name = 'uninstall'
    missing_args_message = 'foo bar'
    subcommands = {
        'apphooks': UninstallApphooksCommand,
        'plugins': UninstallPluginsCommand
    }

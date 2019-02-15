# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.core.management.base import LabelCommand
from django.utils.six.moves import input

from cms.models import Page
from cms.models.pluginmodel import CMSPlugin

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
You have requested to remove %d '%s' apphooks.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (number_of_apphooks, label))
            else:
                confirm = 'yes'
            if confirm == 'yes':
                queryset.update(application_urls=None)
                self.stdout.write("%d '%s' apphooks uninstalled\n" % (number_of_apphooks, label))
        else:
            self.stdout.write("no '%s' apphooks found\n" % label)


class UninstallPluginsCommand(LabelCommand):
    args = 'PLUGIN_NAME'
    command_name = 'plugins'
    label = 'plugin name (eg SamplePlugin)'
    help_string = 'Uninstalls (deletes) specified plugins from the CMSPlugin model'
    missing_args_message = 'foo bar'

    def handle_label(self, label, **options):
        queryset = CMSPlugin.objects.filter(plugin_type=label)
        number_of_plugins = queryset.count()

        if number_of_plugins > 0:
            if options.get('interactive'):
                confirm = input("""
You have requested to remove %d '%s' plugins.
Are you sure you want to do this?
Type 'yes' to continue, or 'no' to cancel: """ % (number_of_plugins, label))
            else:
                confirm = 'yes'
            if confirm == 'yes':
                queryset.delete()
                self.stdout.write("%d '%s' plugins uninstalled\n" % (number_of_plugins, label))
            else:
                self.stdout.write('Aborted')
        else:
            self.stdout.write("no '%s' plugins found\n" % label)


class UninstallCommand(SubcommandsCommand):
    help_string = 'Uninstall objects instances of the following types:'
    command_name = 'uninstall'
    missing_args_message = 'foo bar'
    subcommands = {
        'apphooks': UninstallApphooksCommand,
        'plugins': UninstallPluginsCommand
    }

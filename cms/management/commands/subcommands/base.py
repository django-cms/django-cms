# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from django.core.management.base import BaseCommand


class SubcommandsCommand(BaseCommand):
    subcommands = OrderedDict()
    instances = {}
    stdout = None
    stderr = None
    help_string = ''
    command_name = ''

    def add_arguments(self, parser):
        if self.subcommands:
            subparsers = parser.add_subparsers(dest='cmd')
            for command, cls in self.subcommands.items():
                instance = cls(self.stdout, self.stderr)
                instance.style = self.style
                parser_sub = subparsers.add_parser(
                    cmd=self, name=instance.command_name, help=instance.help_string,
                    description=instance.help_string
                )
                instance.add_arguments(parser_sub)
                self.instances[command] = instance
            super(SubcommandsCommand, self).add_arguments(parser)

    def handle(self, *args, **options):
        if options['cmd'] in self.instances:
            self.instances[options['cmd']].handle(*args, **options)
        else:
            self.print_help('manage.py', 'cms')

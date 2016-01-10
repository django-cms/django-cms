# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from django.core.management.base import BaseCommand, OutputWrapper
from django.core.management.color import no_style


class SubcommandsCommand(BaseCommand):
    subcommands = OrderedDict()
    instances = {}
    stdout = None
    stderr = None
    help_string = ''
    command_name = ''

    subcommand_dest = 'subcmd'

    def add_arguments(self, parser):
        self.instances = {}
        if self.subcommands:
            subparsers = parser.add_subparsers(dest=self.subcommand_dest)
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
        if options[self.subcommand_dest] in self.instances:
            command = self.instances[options[self.subcommand_dest]]
            if options.get('no_color'):
                command.style = no_style()
                command.stderr.style_func = None
            if options.get('stdout'):
                command.stdout = OutputWrapper(options['stdout'])
            if options.get('stderr'):
                command.stderr = OutputWrapper(options.get('stderr'), command.stderr.style_func)
            command.handle(*args, **options)
        else:
            self.print_help('manage.py', 'cms')

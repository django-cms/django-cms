# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals
import os

from collections import OrderedDict

from django.core.management.base import BaseCommand, CommandParser
from django.core.management.color import no_style

from cms.utils.compat import DJANGO_2_0


def add_builtin_arguments(parser):
    parser.add_argument(
        '--noinput',
        action='store_false',
        dest='interactive',
        default=True,
        help='Tells Django CMS to NOT prompt the user for input of any kind.'
    )

    # These are taking "as-is" from Django's management base
    # management command.
    parser.add_argument('-v', '--verbosity', action='store', dest='verbosity', default='1',
        type=int, choices=[0, 1, 2, 3],
        help='Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output')
    parser.add_argument('--settings',
        help=(
            'The Python path to a settings module, e.g. '
            '"myproject.settings.main". If this isn\'t provided, the '
            'DJANGO_SETTINGS_MODULE environment variable will be used.'
        ),
    )
    parser.add_argument('--pythonpath',
        help='A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".')
    parser.add_argument('--traceback', action='store_true',
        help='Raise on CommandError exceptions')
    parser.add_argument('--no-color', action='store_true', dest='no_color', default=False,
        help="Don't colorize the command output.")


class SubcommandsCommand(BaseCommand):
    subcommands = OrderedDict()
    instances = {}
    help_string = ''
    command_name = ''
    stealth_options = ('interactive',)

    subcommand_dest = 'subcmd'

    def create_parser(self, prog_name, subcommand):
        kwargs = {'cmd': self} if DJANGO_2_0 else {}
        parser = CommandParser(
            prog="%s %s" % (os.path.basename(prog_name), subcommand),
            description=self.help or None,
            **kwargs
        )
        self.add_arguments(parser)
        return parser

    def add_arguments(self, parser):
        self.instances = {}

        if self.subcommands:
            stealth_options = set(self.stealth_options)
            subparsers = parser.add_subparsers(dest=self.subcommand_dest)
            for command, cls in self.subcommands.items():
                instance = cls(self.stdout._out, self.stderr._out)
                instance.style = self.style
                kwargs = {'cmd': self} if DJANGO_2_0 else {}
                parser_sub = subparsers.add_parser(
                    name=instance.command_name, help=instance.help_string,
                    description=instance.help_string, **kwargs
                )

                add_builtin_arguments(parser=parser_sub)
                instance.add_arguments(parser_sub)
                stealth_options.update({action.dest for action in parser_sub._actions})
                self.instances[command] = instance
            self.stealth_options = tuple(stealth_options)

    def handle(self, *args, **options):
        if options[self.subcommand_dest] in self.instances:
            command = self.instances[options[self.subcommand_dest]]
            if options.get('no_color'):
                command.style = no_style()
                command.stderr.style_func = None
            if options.get('stdout'):
                command.stdout._out = options.get('stdout')
            if options.get('stderr'):
                command.stderr._out = options.get('stderr')
            command.handle(*args, **options)
        else:
            self.print_help('manage.py', 'cms')

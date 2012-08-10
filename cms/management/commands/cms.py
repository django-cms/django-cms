# -*- coding: utf-8 -*-
from __future__ import absolute_import
from cms.management.commands.subcommands.base import SubcommandsCommand
from cms.management.commands.subcommands.list import ListCommand
from cms.management.commands.subcommands.moderator import ModeratorCommand
from cms.management.commands.subcommands.uninstall import UninstallCommand
from django.core.management.base import BaseCommand
from optparse import make_option
    
    
class Command(SubcommandsCommand):
    
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
        help='Tells django-cms to NOT prompt the user for input of any kind. '),
    )
    
    args = '<subcommand>'

    command_name = 'cms'
    
    subcommands = {
        'uninstall': UninstallCommand,
        'list': ListCommand,
        'moderator': ModeratorCommand,
    }
    
    @property
    def help(self):
        lines = ['django CMS command line interface.', '', 'Available subcommands:']
        for subcommand in sorted(self.subcommands.keys()):
            lines.append('  %s' % subcommand)
        lines.append('')
        lines.append('Use `manage.py cms <subcommand> --help` for help about subcommands')
        return '\n'.join(lines)
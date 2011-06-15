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

    command_name = 'cms'
    
    help = 'Various django-cms commands'
    subcommands = {
        'uninstall': UninstallCommand,
        'list': ListCommand,
        'moderator': ModeratorCommand,
    }
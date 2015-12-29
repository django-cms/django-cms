# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from collections import OrderedDict

from .subcommands.base import SubcommandsCommand
from .subcommands.check import CheckInstallation
from .subcommands.list import ListCommand
from .subcommands.moderator import ModeratorCommand
from .subcommands.publisher_publish import PublishCommand
from .subcommands.tree import FixTreeCommand
from .subcommands.uninstall import UninstallCommand
from .subcommands.copy_lang import CopyLangCommand
from .subcommands.copy_site import CopySiteCommand
from .subcommands.delete_orphaned_plugins import DeleteOrphanedPluginsCommand


class Command(SubcommandsCommand):
    command_name = 'cms'
    subcommands = OrderedDict((
        ('check', CheckInstallation),
        ('copy-lang', CopyLangCommand),
        ('copy-site', CopySiteCommand),
        ('delete-orphaned-plugins', DeleteOrphanedPluginsCommand),
        ('fix-tree', FixTreeCommand),
        ('list', ListCommand),
        ('moderator', ModeratorCommand),
        ('publisher-publish', PublishCommand),
        ('uninstall', UninstallCommand),
    ))
    missing_args_message = 'one of the available sub commands must be provided'

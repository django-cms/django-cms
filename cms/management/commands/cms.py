from collections import OrderedDict

import cms

from .subcommands.base import SubcommandsCommand
from .subcommands.check import CheckInstallation
from .subcommands.copy import CopyCommand
from .subcommands.delete_orphaned_plugins import DeleteOrphanedPluginsCommand
from .subcommands.list import ListCommand
from .subcommands.tree import FixTreeCommand
from .subcommands.uninstall import UninstallCommand


class Command(SubcommandsCommand):
    command_name = 'cms'
    subcommands = OrderedDict((
        ('check', CheckInstallation),
        ('copy', CopyCommand),
        ('delete-orphaned-plugins', DeleteOrphanedPluginsCommand),
        ('fix-tree', FixTreeCommand),
        ('list', ListCommand),
        ('uninstall', UninstallCommand),
    ))
    missing_args_message = 'one of the available sub commands must be provided'

    subcommand_dest = 'cmd'

    def get_version(self):
        return cms.__version__

    def add_arguments(self, parser):
        parser.add_argument('--version', action='version', version=self.get_version())
        super().add_arguments(parser)

# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand, CommandError
import sys



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
import os
import sys

from django.core.checks.security.base import SECRET_KEY_INSECURE_PREFIX
from django.core.management import load_command_class
from django.core.management.utils import get_random_secret_key


class CMSCommandLineUtility:
    commands = {"startproject": "cms"}

    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])
        if self.prog_name == "__main__.py":
            self.prog_name = "python -m cms"

    def execute(self):
        command = load_command_class("cms", "startproject")
        if self.argv[1:] == ["--version"]:
            from cms import __version__
            sys.stdout.write(__version__)
        elif  self.argv[1:] == ["--help"]:
            command.print_help(self.prog_name, "")
        else:
            command.run_from_argv([self.argv[0], ""] + self.argv[1:])  #  fake"empty" subcommand


def execute_from_command_line(argv=None):
    """Run a ManagementUtility."""
    utility = CMSCommandLineUtility(argv)
    utility.execute()

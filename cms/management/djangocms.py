import os
import sys

from django.core.management import load_command_class


def execute_from_command_line(argv=None):
    """Run the startcmsproject management command."""

    # Prepare arguments
    argv = argv or sys.argv[:]
    argv[0] = os.path.basename(argv[0])
    if argv[0] == "__main__.py":
        argv[0] = "python -m cms"

    # Find command
    command = load_command_class("cms", "startcmsproject")
    if argv[1:] == ["--version"]:
        from cms import __version__
        sys.stdout.write(__version__ + "\n")
    elif argv[1:] == ["--help"]:
        command.print_help(argv[0], "")
    else:
        command.run_from_argv([argv[0], ""] + argv[1:])  # fake "empty" subcommand

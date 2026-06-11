#!/usr/bin/env python
import argparse
import os
import shutil
import subprocess
import sys

from django.core.checks.security.base import SECRET_KEY_INSECURE_PREFIX
from django.core.management import CommandError
from django.core.management.templates import TemplateCommand
from django.core.management.utils import get_random_secret_key

from cms import __version__ as cms_version


class Command(TemplateCommand):
    help = (
        "Creates a django CMS project directory structure for the given project "
        "name in the current directory or optionally in the given directory."
    )
    missing_args_message = "You must provide a project name."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Version major.minor
        self.major_minor = ".".join(cms_version.split(".")[:2])

        # Configure formatting
        self.HEADING = lambda text: "\n" + self.style.SQL_FIELD(text)
        self.COMMAND = self.style.HTTP_SUCCESS

    # Effective defaults for the project options. The arguments themselves
    # default to ``None`` so that ``--interactive`` can tell apart an option
    # that was given on the command line from one that needs to be asked for.
    OPTION_DEFAULTS = {
        "mode": "traditional",
        "versioning": True,
        "moderation": False,
        "alias": True,
        "stories": False,
    }

    def create_parser(self, *args, **kwargs):
        parser = super().create_parser(*args, **kwargs)
        # Allow running with no arguments at all: a missing project name drops
        # into interactive mode instead of erroring out. handle() still reports
        # a missing name when input is suppressed with --noinput.
        parser.missing_args_message = None
        return parser

    def add_arguments(self, parser):
        super().add_arguments(parser)
        # Make the project name optional so it can be asked for in interactive
        # mode; a missing name is reported by handle() otherwise.
        for action in parser._actions:
            if action.dest == "name":
                action.nargs = "?"
                break
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Tells django CMS to NOT prompt the user for input of any kind. "
                "Superusers created with --noinput will "
                "not be able to log in until they're given a valid password."
            ),
        )
        parser.add_argument(
            "--interactive",
            action="store_true",
            dest="prompt",
            default=False,
            help=(
                "Ask for the project name and any option not given on the command line. "
                "Interactive mode is also entered automatically when no project name is "
                "given (unless --noinput is used)."
            ),
        )
        parser.add_argument(
            "--username",
            help="Specifies the login for the superuser to be created",
        )
        parser.add_argument("--email", help="Specifies the email for the superuser to be created")
        parser.add_argument(
            "--stories",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds the stories component library (djangocms-stories) to the project (default: off)",
        )
        parser.add_argument(
            "--mode",
            choices=("traditional", "headless", "hybrid"),
            default=None,
            help="Selects the CMS mode: traditional, headless or hybrid (default: traditional).",
        )
        parser.add_argument(
            "--versioning",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds content versioning (djangocms-versioning) to the project (default: on).",
        )
        parser.add_argument(
            "--moderation",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds content moderation (djangocms-moderation) to the project (default: off).",
        )
        parser.add_argument(
            "--alias",
            action=argparse.BooleanOptionalAction,
            default=None,
            help="Adds reusable aliases (djangocms-alias) to the project (default: on).",
        )

    def get_default_template(self):
        return f"https://github.com/django-cms/cms-template/archive/{self.major_minor}.tar.gz"

    def postprocess(self, project, options):
        # Go to project dir
        self.write_command(f'cd "{project}"')
        os.chdir(project)

        # Install requirements
        self.install_requirements(project)

        # Create database by running migrations
        self.stdout.write(self.HEADING("Run migrations"))
        self.run_management_command(["migrate"], capture_output=True)

        # Create superuser (respecting command line arguments)
        self.stdout.write(self.HEADING("Create superuser"))
        command = ["createsuperuser"]
        if options.get("username"):
            command.append("--username")
            command.append(options.get("username"))
        if options.get("email"):
            command.append("--email")
            command.append(options.get("email"))
        if not options["interactive"]:
            if "--username" not in command:
                command.append("--username")
                command.append(os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin"))
            if "--email" not in command:
                command.append("--email")
                command.append(os.environ.get("DJANGO_SUPERUSER_EMAIL", "none@nowhere.com"))
            command.append("--noinput")
        self.run_management_command(command)

        # Check installation
        self.stdout.write(self.HEADING("Check installation"))
        self.run_management_command(["cms", "check"], capture_output=True)

        # Display success message
        message = f"django CMS {cms_version} installed successfully"
        separator = "*" * len(message)
        self.stdout.write(self.HEADING(f"{separator}\n{message}\n{separator}"))
        self.stdout.write(
            f"""
Congratulations! You have successfully installed django CMS,
the lean enterprise content management powered by Django!

Now, to start the development server first go to your newly
created project and then call the runserver management command:
$ {self.style.SUCCESS("cd " + project)}
$ {self.style.SUCCESS("python -m manage runserver")}

Learn more at https://docs.django-cms.org/
Join the django CMS Discord Server at https://discord-main-channel.django-cms.org

Enjoy!
"""
        )

    def install_requirements(self, project):
        for req_file in ("requirements.txt", "requirements.in"):
            requirements = os.path.join(project, req_file)
            if os.path.isfile(requirements):
                if self.running_in_venv() or os.environ.get("DJANGOCMS_ALLOW_PIP_INSTALL", "False") == "True":
                    self.stdout.write(self.HEADING(f"Install requirements in {requirements}"))
                    self.write_command(f'python -m pip install -r "{requirements}"')
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", requirements],
                        capture_output=True, check=False,
                    )
                    if result.returncode:
                        self.stderr.write(self.style.ERROR(result.stderr.decode()))
                        raise CommandError(f"Failed to install requirements in {requirements}")
                    break
                else:
                    self.stderr.write(
                        self.style.ERROR(
                            "To automatically install requirements for your new django CMS "
                            "project use this command in an virtual environment."
                        )
                    )
                    raise CommandError("Requirements not installed")

    def run_management_command(self, commands, capture_output=False):
        self.write_command("python -m manage " + " ".join(commands))
        result = subprocess.run([sys.executable, "-m", "manage"] + commands, capture_output=capture_output, check=False)
        if result.returncode:
            if capture_output:
                self.stderr.write(self.style.ERROR(result.stderr.decode()))
            raise CommandError(f"{sys.executable} -m manage {' '.join(commands)} failed.")

    def write_command(self, command):
        self.stderr.write(self.COMMAND(command))

    @staticmethod
    def running_in_venv():
        return sys.prefix != sys.base_prefix

    def handle_template(self, template, subdir):
        if not template:
            template = self.get_default_template()
        return super().handle_template(template, subdir)

    def ask(self, label, default=None):
        suffix = f" [{default}]" if default not in (None, "") else ""
        return input(f"{label}{suffix}: ").strip() or default

    def ask_choice(self, label, choices, default):
        while True:
            value = self.ask(f"{label} ({'/'.join(choices)})", default)
            if value in choices:
                return value
            self.stderr.write(self.style.ERROR(f"Please choose one of: {', '.join(choices)}"))

    def ask_bool(self, label, default):
        while True:
            value = self.ask(f"{label} (yes/no)", "yes" if default else "no").lower()
            if value in ("y", "yes", "true", "1", "on"):
                return True
            if value in ("n", "no", "false", "0", "off"):
                return False
            self.stderr.write(self.style.ERROR("Please answer yes or no."))

    def prompt_for_options(self, name, options):
        """Ask for the project name and any option still unset (``None``)."""
        self.stdout.write(self.HEADING(f"Create django CMS {cms_version} project"))
        if not name:
            while not name:
                name = self.ask("Project name")
                if not name:
                    self.stderr.write(self.style.ERROR("A project name is required."))
        if options.get("mode") is None:
            options["mode"] = self.ask_choice(
                "CMS mode", ("traditional", "headless", "hybrid"), self.OPTION_DEFAULTS["mode"]
            )
        if options.get("versioning") is None:
            options["versioning"] = self.ask_bool("Enable content versioning", self.OPTION_DEFAULTS["versioning"])
        if options.get("moderation") is None:
            # Moderation builds on top of versioning, so only offer it when
            # versioning is enabled; otherwise it stays off.
            options["moderation"] = (
                self.ask_bool("Enable content moderation", self.OPTION_DEFAULTS["moderation"])
                if options["versioning"]
                else False
            )
        if options.get("alias") is None:
            options["alias"] = self.ask_bool("Add reusable aliases", self.OPTION_DEFAULTS["alias"])
        if options.get("stories") is None:
            options["stories"] = self.ask_bool("Add the stories component library", self.OPTION_DEFAULTS["stories"])
        return name

    def handle(self, **options):
        # Capture target and name for postprocessing
        name = options.pop("name", None)
        directory = options.pop("directory", None)

        # Interactively ask for the project name and any option not provided.
        # Prompting is enabled explicitly via --interactive, or implicitly when
        # no project name was given (unless input is suppressed with --noinput).
        prompt = options.pop("prompt", False) or (not name and options.get("interactive", True))
        if prompt:
            name = self.prompt_for_options(name, options)

        # Fill in the effective defaults for any option not given (and not
        # asked for interactively).
        for key, value in self.OPTION_DEFAULTS.items():
            if options.get(key) is None:
                options[key] = value

        if not name:
            raise CommandError(self.missing_args_message)

        # Content moderation builds on top of content versioning.
        if options["moderation"] and not options["versioning"]:
            raise CommandError("--moderation requires versioning; remove --no-versioning or drop --moderation.")

        # Create a random SECRET_KEY to put it in the main settings.
        options["secret_key"] = SECRET_KEY_INSECURE_PREFIX + get_random_secret_key()

        self.stdout.write(self.HEADING("Clone template using django-admin"))
        command = (
            f'django-admin startproject "{name}" ' f'--template {options["template"] or self.get_default_template()}'
        )
        if directory:
            command += f' --directory "{directory}"'
        self.write_command(command)

        if directory is None:
            top_dir = os.path.join(os.getcwd(), name)
        else:
            top_dir = os.path.abspath(os.path.expanduser(directory))
        # Only a directory created by this run may be cleaned up on failure;
        # an existing target (django-admin renders into it) is left untouched.
        created_dir = directory is None and not os.path.exists(top_dir)
        original_cwd = os.getcwd()

        try:
            # Run startproject command
            super().handle(
                "project", name, directory, cms_version=cms_version, cms_docs_version=self.major_minor, **options
            )
            self.postprocess(top_dir, options)
        except BaseException:
            # Remove the partially created project if the command fails or is
            # interrupted (e.g. Ctrl-C), but only when we created the directory.
            if created_dir and os.path.isdir(top_dir):
                os.chdir(original_cwd)
                self.stderr.write(self.style.WARNING(f"Removing partially created project at {top_dir}"))
                shutil.rmtree(top_dir, ignore_errors=True)
            raise

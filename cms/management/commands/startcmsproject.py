#!/usr/bin/env python
import os
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

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Tells Django to NOT prompt the user for input of any kind. "
                "Superusers created with --noinput will "
                "not be able to log in until they're given a valid password."
            ),
        )

    def get_default_template(self):
        from cms import __version__

        version = ".".join(__version__.split(".")[:2])  # get major.minor
        return f"https://github.com/django-cms/cms-template/archive/{version}.tar.gz"

    def postprocess(self, project, options):
        self.HEADING = self.style.SQL_FIELD
        self.install_requirements(project)
        os.chdir(project)
        self.stdout.write(self.HEADING("Create migrations"))
        self.run_management_command(["migrate"], capture_output=True)
        self.stdout.write(self.HEADING("Create superuser"))
        if options["interactive"]:
            self.run_management_command(["createsuperuser"])
        else:
            username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "admin")
            usermail = os.environ.get("DJANGO_SUPERUSER_EMAIL", "none@nowhere.com")
            self.run_management_command([
                "createsuperuser", "--username", username, "--email", usermail, "--noinput"]
            )
        self.stdout.write(self.HEADING("Check installation"))
        self.run_management_command(["cms", "check"])

        message = f"django CMS {cms_version} installed successfully"
        separator = "=" * len(message)
        self.stdout.write(self.HEADING(f"{separator}\n{message}\n{separator}"))
        self.stdout.write(f"""
Congratulations! You have successfully installed django CMS,
the lean enterprise content management powered by Django!

Now, to start the development server first go to your newly
created project:
$ {self.style.SUCCESS("cd " + project)}
$ {self.style.SUCCESS("python manage.py runserver")}

Learn more at https://docs.django-cms.org/
Join the django CMS Slack channel http://www.django-cms.org/slack

Enjoy!
""")

    def install_requirements(self, project):
        for req_file in ("requirements.txt", "requirements.in"):
            requirements = os.path.join(project, req_file)
            if os.path.isfile(requirements):
                if self.running_in_venv() or os.environ.get("DJANGOCMS_ALLOW_PIP_INSTALL", "False") == "True":
                    self.stdout.write(self.HEADING(f"Installing requirements in {requirements}"))
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", requirements],
                        capture_output=True,
                    )
                    if result.returncode:
                        self.stderr.write(self.style.ERROR(result.stderr.decode()))
                        raise CommandError(f"Failed to install requirements in {requirements}")
                    break
                else:
                    self.stdout(self.style.ERROR("To automatically install requirements for your new django CMS "
                                "project use this command in an virtual environment."))
                    raise CommandError("Requirements not installed")

    def run_management_command(self, commands, capture_output=False):
        result = subprocess.run(
            [sys.executable, "manage.py"] + commands,
            capture_output=capture_output
        )
        if result.returncode:
            if capture_output:
                self.stderr.write(self.style.ERROR(result.stderr.decode()))
            raise CommandError(f"{sys.executable} manage.py {' '.join(commands)} failed.")

    @staticmethod
    def running_in_venv():
        return sys.prefix != sys.base_prefix

    def handle_template(self, template, subdir):
        if not template:
            template = self.get_default_template()
        return super().handle_template(template, subdir)

    def handle(self, **options):
        # Capture target and name for postprocessing
        name = options.pop("name")
        directory = options.pop("directory", None)
        # Create a random SECRET_KEY to put it in the main settings.
        options["secret_key"] = SECRET_KEY_INSECURE_PREFIX + get_random_secret_key()
        super().handle("project", name, directory, **options)
        if directory is None:
            top_dir = os.path.join(os.getcwd(), name)
        else:
            top_dir = os.path.abspath(os.path.expanduser(directory))
        self.postprocess(top_dir, options)

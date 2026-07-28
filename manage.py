#!/usr/bin/env python
import os
import sys
import warnings

from cms.exceptions import DontUsePageAttributeWarning

warnings.filterwarnings("ignore", category=DontUsePageAttributeWarning)


def consume_option(argv, name):
    """Pop ``--name value`` from ``argv`` and return the value (or ``None``)."""
    if name in argv:
        pos = argv.index(name)
        if len(argv) > pos + 1:
            value = argv[pos + 1]
            argv.pop(pos)
            argv.pop(pos)
            return value
        raise ValueError(f"No value provided for {name}")
    return None


def main(argv):
    from django.core.management import execute_from_command_line

    local_commands = [
        "test",
        "migrate",
        "makemigrations",
    ]

    if (
        len(argv) > 1
        and argv[1] in local_commands
        and len(argv) - sum((arg.startswith("-") for arg in argv[2:]), start=0) < 3
    ):
        argv.append("cms")
        argv.append("menus")

    execute_from_command_line(argv)


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_LIVE_TEST_SERVER_ADDRESS", "localhost:8000-9000")
    os.environ.setdefault("DJANGO_TESTS", "1")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.tests.settings")

    argv = sys.argv

    # The settings live in cms/tests/settings.py. The historical command line
    # options are mapped onto the environment variables that module reads.
    auth_user_model = consume_option(argv, "--auth-user-model")
    if auth_user_model:
        os.environ["AUTH_USER_MODEL"] = auth_user_model

    db_url = consume_option(argv, "--db-url")
    if db_url:
        os.environ["DATABASE_URL"] = db_url

    if "--use-tz" in argv:
        os.environ["USE_TZ"] = "1"
        argv.pop(argv.index("--use-tz"))

    main(argv)

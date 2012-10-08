#!/usr/bin/env python
from cms.test_utils.cli import configure
from cms.test_utils.tmpdir import temp_dir
import os
import sys

if __name__ == "__main__":
    with temp_dir() as STATIC_ROOT:
        with temp_dir() as MEDIA_ROOT:
            configure(
                ROOT_URLCONF='cms.test_utils.project.urls',
                STATIC_ROOT=STATIC_ROOT,
                MEDIA_ROOT=MEDIA_ROOT,
                DATABASES = {
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': 'cmstestdb.sqlite',
                        }
                }
            )

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.test_utils.cli")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)

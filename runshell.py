#!/usr/bin/env python
import os
from cms.test_utils.cli import configure
from cms.test_utils.tmpdir import temp_dir


def main():
    with temp_dir() as STATIC_ROOT:
        with temp_dir() as MEDIA_ROOT:
            configure(
                os.environ.get('DATABASE_URL', 'sqlite://localhost/cmstestdb.sqlite'),
                ROOT_URLCONF='cms.test_utils.project.urls',
                STATIC_ROOT=STATIC_ROOT,
                MEDIA_ROOT=MEDIA_ROOT,
            )
            from django.core.management import call_command
            call_command('shell')

if __name__ == '__main__':
    main()

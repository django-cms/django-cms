from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings


class MigrationTestCase(TestCase):

    @override_settings(MIGRATION_MODULES={})
    def test_for_missing_migrations(self):
        output = StringIO()
        options = {
            'interactive': False,
            'dry_run': True,
            'stdout': output,
            'check_changes': True,
        }

        try:
            call_command('makemigrations', 'cms', **options)
        except SystemExit as e:
            status_code = str(e)
        else:
            # the "no changes" exit code is 0
            status_code = '0'

        if status_code == '1':
            self.fail(f'There are missing migrations:\n {output.getvalue()}')

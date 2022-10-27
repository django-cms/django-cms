import io

from django.core.management import call_command
from django.test import TestCase, override_settings


class MigrationTestCase(TestCase):

    @override_settings(MIGRATION_MODULES={})
    def test_for_missing_migrations(self):
        output = io.StringIO()
        options = {
            'interactive': False,
            'dry_run': True,
            'stdout': output,
            'check_changes': True,
        }

        try:
            # Django 4.1 introduces a new migration to djangocms_text_ckeditor
            # therefore only check for own migrations
            call_command('makemigrations', 'cms', **options)
        except SystemExit as e:
            status_code = str(e)
        else:
            # the "no changes" exit code is 0
            status_code = '0'

        if status_code == '1':
            self.fail('There are missing migrations:\n {}'.format(output.getvalue()))

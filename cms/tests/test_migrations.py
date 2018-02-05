from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils.six import text_type
from django.utils.six.moves import StringIO

from cms.utils.compat import DJANGO_1_9

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

        if DJANGO_1_9:
            # this option was deprecated in Django 1.10
            options['exit_code'] = True
            # this option was introduced in Django 1.10
            del options['check_changes']

        try:
            call_command('makemigrations', **options)
        except SystemExit as e:
            status_code = text_type(e)
        else:
            # on Django < 1.10, the "no changes" exit code is 1
            # on Django > 1.10, the "no changes" exit code is 0
            status_code = '1' if DJANGO_1_9 else '0'

        if status_code == '0' and DJANGO_1_9:
            self.fail('There are missing migrations:\n {}'.format(output.getvalue()))

        if status_code == '1' and not DJANGO_1_9:
            self.fail('There are missing migrations:\n {}'.format(output.getvalue()))

# -*- coding: utf-8 -*-
import tempfile
import codecs

try:
    from cStringIO import StringIO
except:
    from io import StringIO

from django.core.management import call_command

from cms.test_utils.fixtures.navextenders import NavextendersFixture
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.models import Page


class FixtureTestCase(NavextendersFixture, SettingsOverrideTestCase):
    settings_overrides = {
        'USE_TZ': False
    }

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_fixture_load(self):
        output = StringIO()
        dump = tempfile.mkstemp(".json")
        call_command('dumpdata', 'cms', indent=3, stdout=output)
        Page.objects.all().delete()
        output.seek(0)
        with codecs.open(dump[1], 'w', 'utf-8') as dumpfile:
            dumpfile.write(output.read())

        self.assertEqual(0, Page.objects.count())
        call_command('loaddata', dump[1], commit=False, stdout=output)
        self.assertEqual(10, Page.objects.count())

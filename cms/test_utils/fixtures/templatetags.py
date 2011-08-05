# -*- coding: utf-8 -*-
from __future__ import with_statement
from cms.api import create_page, create_title
from cms.test_utils.util.context_managers import SettingsOverride


class TwoPagesFixture(object):
    def create_fixtures(self):
        defaults = {
            'template': 'nav_playground.html',
            'published': True,
            'in_navigation': True,
        }
        with SettingsOverride(CMS_MODERATOR=False, CMS_PERMISSION=False):
            first = create_page('first', language='en', **defaults)
            create_title('de', 'erste', first)
            second = create_page('second', language='en', reverse_id='myreverseid', **defaults)
            create_title('de', 'zweite', second)
            
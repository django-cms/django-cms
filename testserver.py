#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import sys

def noop_gettext(s):
    return s

gettext = noop_gettext


HELPER_SETTINGS = dict(
    LANGUAGES=(
        ('en', u'English'),
        ('de', u'Deutsch'),
    ),
    LANGUAGE_CODE='en',
    PARLER_LANGUAGES={
        1: (
            {'code': 'en', 'fallbacks': ['de',]},
            {'code': 'de', 'fallbacks': ['en',]},
        ),
        'default': {
            'fallback': 'en',
            'hide_untranslated': False,
        },
    },
    PARLER_ENABLE_CACHING=False,
    CMS_LANGUAGES={
        1: [
            {
                'code': 'en',
                'name': gettext('English'),
                'fallbacks': ['de',],
            },
            {
                'code': 'de',
                'name': gettext('German'),
                'fallbacks': ['en',],
            },
        ],
        'default': {
            'fallbacks': ['en', 'de',],
            'redirect_on_fallback': False,
            'public': True,
            'hide_untranslated': False,
        }
    }
)


def run():
    from djangocms_helper import runner

    os.environ.setdefault('DATABASE_URL', 'sqlite://localhost/testdb.sqlite')

    # remvove the test DB file if we use sqlite
    db_url = os.environ.get('DATABASE_URL')
    db_file = os.path.split(db_url)[-1]
    if db_url.startswith('sqlite://localhost') and os.path.exists(db_file):
        os.remove(db_file)

    # we use '.runner()', not '.cms()' nor '.run()' because it does not
    # add 'test' argument implicitly
    runner.runner([sys.argv[0], 'cms', '--cms', 'server'])

if __name__ == "__main__":
    run()

from cms.test_utils.util.context_managers import SettingsOverride
from django.conf import settings
from django.core.management import call_command
from django.db import connections
import os


class Fixture(object):
    DB_OVERRIDE = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }

    def __init__(self, name, **settings_overrides):
        self.name = name
        self.settings_overrides = settings_overrides
        
    def start(self):
        self.so = SettingsOverride(**self.settings_overrides)
        self.so.__enter__()
        self.old_db = connections.databases['default'] 
        connections.databases['default'] = self.DB_OVERRIDE
        call_command('syncdb', migrate_all=True, interactive=False, verbosity=0)
    
    def save(self):
        filename = os.path.join(settings.FIXTURE_DIRS[0], self.name)
        with open(filename, 'wb') as fobj:
            call_command('dumpdata', 'cms', stdout=fobj)
        self.so.__exit__(None, None, None)
        connections.databases['default'] = self.old_db
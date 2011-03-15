from cms.test_utils.util.context_managers import SettingsOverride # pragma: no cover
from django.conf import settings # pragma: no cover
from django.core.management import call_command # pragma: no cover
from django.db import connections # pragma: no cover
import os # pragma: no cover


class Fixture(object): # pragma: no cover
    DB_OVERRIDE = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }

    def __init__(self, name, apps=['cms'], **settings_overrides):
        self.name = name
        self.apps = apps
        self.settings_overrides = settings_overrides
        
    def start(self):
        self.so = SettingsOverride(**self.settings_overrides)
        self.so.__enter__()
        self.old_db = connections.databases['default'] 
        connections.databases['default'] = self.DB_OVERRIDE
        if 'default' in connections._connections:
            del connections._connections['default']
        call_command('syncdb', migrate_all=True, interactive=False, verbosity=0)
    
    def save(self):
        filename = os.path.join(settings.FIXTURE_DIRS[0], self.name)
        with open(filename, 'wb') as fobj:
            call_command('dumpdata', *self.apps, stdout=fobj)
        self.so.__exit__(None, None, None)
        connections.databases['default'] = self.old_db
        if 'default' in connections._connections:
            del connections._connections['default']
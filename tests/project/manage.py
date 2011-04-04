#!/usr/bin/env python
import sys
import os
appdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
projectdir = os.path.abspath(os.path.join(appdir, '../'))
sys.path = [projectdir, appdir] + sys.path
from django.core.management import execute_manager
try:
    import settings # Assumed to be in the same directory.
except ImportError: # pragma: no cover 
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(settings)

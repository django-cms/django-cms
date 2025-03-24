import os
import django

# Ensure settings are loaded before tests run
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cms.settings")
django.setup()

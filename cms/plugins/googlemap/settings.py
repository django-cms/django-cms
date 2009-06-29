from django.conf import settings

GOOGLE_MAPS_API_KEY = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
# -*- coding: utf-8 -*-
from django.conf import settings

# Settings for CMS Toolbar
CMS_TOOLBAR_URL__EDIT_ON = getattr(settings, 'CMS_TOOLBAR_URL__EDIT_ON', 'edit')
CMS_TOOLBAR_URL__EDIT_OFF = getattr(settings, 'CMS_TOOLBAR_URL__EDIT_OFF', 'edit_off')
CMS_TOOLBAR_URL__BUILD = getattr(settings, 'CMS_TOOLBAR_URL__BUILD', 'build')
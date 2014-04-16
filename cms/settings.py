# -*- coding: utf-8 -*-
from django.conf import settings

# Settings for CMS Toolbar
CMS_ADMIN_TOOLBAR__EDIT_ON = getattr(settings, 'CMS_ADMIN_TOOLBAR__EDIT_ON', 'edit')
CMS_ADMIN_TOOLBAR__EDIT_OFF = getattr(settings, 'CMS_ADMIN_TOOLBAR__EDIT_OFF', 'edit_off')
CMS_ADMIN_TOOLBAR__BUILD = getattr(settings, 'CMS_ADMIN_TOOLBAR__BUILD', 'build')
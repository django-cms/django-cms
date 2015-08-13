# -*- coding: utf-8 -*-
from .settingmodels import *  # nopyflakes
from .pagemodel import *  # nopyflakes
from .permissionmodels import *  # nopyflakes
from .placeholdermodel import *  # nopyflakes
from .pluginmodel import *  # nopyflakes
from .titlemodels import *  # nopyflakes
from .placeholderpluginmodel import *  # nopyflakes
from .static_placeholder import *  # nopyflakes
from .aliaspluginmodel import *  # nopyflakes
from .apphooks_reload import *  # nopyflakes
# must be last
from cms import signals as s_import  # nopyflakes


# Temporary support for django version 1.6 and below
from cms.utils.compat import DJANGO_1_6

if DJANGO_1_6:
    from cms.utils.setup import setup
    setup()

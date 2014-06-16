# -*- coding: utf-8 -*-
import warnings

from django import template

from cms.templatetags.cms_tags import RenderPlaceholder

warnings.warn('render_placeholder is now located in cms_tags. Please do not '
              'load placeholder_tags anymore.', DeprecationWarning)

register = template.Library()

register.tag(RenderPlaceholder)


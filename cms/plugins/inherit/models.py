from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page

class InheritPagePlaceholder(CMSPlugin):
    """
    Provides the ability to inherit plugins for a certain placeholder from an associated "parent" page instance
    """
    parent_page = models.ForeignKey(Page, null=False, help_text=_("Choose a page to include its plugins into this placeholder"))


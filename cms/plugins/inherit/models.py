from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin, Page
from django.conf import settings

class InheritPagePlaceholder(CMSPlugin):
    """
    Provides the ability to inherit plugins for a certain placeholder from an associated "parent" page instance
    """
    from_page = models.ForeignKey(Page, null=True, blank=True, help_text=_("Choose a page to include its plugins into this placeholder, empty will choose current page"))
    from_language = models.CharField(_("language"), max_length=5, choices=settings.CMS_LANGUAGES, blank=True, null=True, help_text=_("Optional: the language of the plugins you want"))

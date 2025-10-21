"""
Signal handlers for PageContent model operations.
"""
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from cms.models.contentmodels import PageContent
from cms.signals.apphook import set_restart_trigger

logger = logging.getLogger(__name__)


@receiver(post_save, sender=PageContent)
def handle_pagecontent_post_save(sender, instance, created, **kwargs):
    """
    Handle PageContent post_save signal.

    When a new PageContent (language variant) is created for a page that has
    an apphook, we need to trigger URL reloading to ensure the apphook URLs
    are available for the new language.

    This fixes the issue where creating a new language variant for a page
    with an apphook causes NoReverseMatch exceptions until the server is
    restarted.
    """
    if created and instance.page.application_urls:
        # A new language variant was created for a page with an apphook
        # Trigger URL reloading to make apphook URLs available for this
        # language
        logger.debug(
            f"New language variant '{instance.language}' created for page "
            f"'{instance.page}' with apphook "
            f"'{instance.page.application_urls}'. Triggering URL reload."
        )
        set_restart_trigger()
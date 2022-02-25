from django.db.models.signals import pre_migrate
from django.dispatch import receiver

from cms.exceptions import ConfirmationOfVersion4Required
from cms.utils.conf import get_cms_setting


@receiver(pre_migrate)
def check_v4_confirmation(**kwargs):
    """Signal handler to get the confirmation that using version 4 is intentional"""
    if not get_cms_setting('CONFIRM_VERSION4'):
        raise ConfirmationOfVersion4Required(
            "You must confirm your intention to use django-cms version 4 with the setting CMS_CONFIRM_VERSION4"
        )

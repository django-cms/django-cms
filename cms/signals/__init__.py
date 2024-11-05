from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db.models import signals
from django.db.models.signals import pre_migrate
from django.dispatch import Signal, receiver

from cms.exceptions import ConfirmationOfVersion4Required
from cms.models import (
    GlobalPagePermission,
    PagePermission,
    PageUser,
    PageUserGroup,
)
from cms.signals.apphook import debug_server_restart, trigger_server_restart
from cms.signals.log_entries import (
    log_page_operations,
    log_placeholder_operations,
)
from cms.signals.permissions import (
    post_save_user,
    post_save_user_group,
    pre_delete_globalpagepermission,
    pre_delete_group,
    pre_delete_pagepermission,
    pre_delete_user,
    pre_save_globalpagepermission,
    pre_save_group,
    pre_save_pagepermission,
    pre_save_user,
    user_m2m_changed,
)
from cms.utils.conf import get_cms_setting


@receiver(pre_migrate)
def check_v4_confirmation(**kwargs):
    """
    Signal handler to get the confirmation that using version 4 is intentional.

    This is a temporary step to ensure people only migrate their databases intentionally.
    """
    if not get_cms_setting('CONFIRM_VERSION4'):
        raise ConfirmationOfVersion4Required(
            "You must confirm your intention to use django-cms version 4 with the setting CMS_CONFIRM_VERSION4"
        )

# ################### Our own signals ###################


# fired after page location is changed - is moved from one node to other
page_moved = Signal()

# fired if a public page with an apphook is added or changed
urls_need_reloading = Signal()

# *disclaimer*
# The generic object operation signals are very likely to change
# as their usage evolves.
# As a result, rely on these at your own risk
pre_obj_operation = Signal()

post_obj_operation = Signal()

pre_placeholder_operation = Signal()

post_placeholder_operation = Signal()


# ################## apphook reloading ###################

if settings.DEBUG:
    urls_need_reloading.connect(debug_server_restart)


urls_need_reloading.connect(
    trigger_server_restart,
    dispatch_uid='aldryn-apphook-reload-handle-urls-need-reloading'
)


# ##################### log entries #######################

post_obj_operation.connect(log_page_operations)
post_placeholder_operation.connect(log_placeholder_operations)

# ##################### permissions #######################

if get_cms_setting('PERMISSION'):
    # only if permissions are in use
    signals.pre_save.connect(pre_save_user, sender=User, dispatch_uid='cms_pre_save_user')
    signals.post_save.connect(post_save_user, sender=User, dispatch_uid='cms_post_save_user')
    signals.pre_delete.connect(pre_delete_user, sender=User, dispatch_uid='cms_pre_delete_user')
    signals.m2m_changed.connect(user_m2m_changed, sender=User.groups.through, dispatch_uid='cms_user_m2m_changed')

    signals.pre_save.connect(pre_save_user, sender=PageUser, dispatch_uid='cms_pre_save_pageuser')
    signals.pre_delete.connect(pre_delete_user, sender=PageUser, dispatch_uid='cms_pre_delete_pageuser')

    signals.pre_save.connect(pre_save_group, sender=Group, dispatch_uid='cms_pre_save_group')
    signals.post_save.connect(post_save_user_group, sender=Group, dispatch_uid='cms_post_save_group')
    signals.pre_delete.connect(pre_delete_group, sender=Group, dispatch_uid='cms_post_save_group')

    signals.pre_save.connect(pre_save_group, sender=PageUserGroup, dispatch_uid='cms_pre_save_pageusergroup')
    signals.pre_delete.connect(pre_delete_group, sender=PageUserGroup, dispatch_uid='cms_pre_delete_pageusergroup')

    signals.pre_save.connect(
        pre_save_pagepermission, sender=PagePermission, dispatch_uid='cms_pre_save_pagepermission'
    )
    signals.pre_delete.connect(
        pre_delete_pagepermission, sender=PagePermission, dispatch_uid='cms_pre_delete_pagepermission'
    )

    signals.pre_save.connect(
        pre_save_globalpagepermission, sender=GlobalPagePermission, dispatch_uid='cms_pre_save_globalpagepermission'
    )
    signals.pre_delete.connect(
        pre_delete_globalpagepermission, sender=GlobalPagePermission,
        dispatch_uid='cms_pre_delete_globalpagepermission'
    )

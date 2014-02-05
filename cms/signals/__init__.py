# -*- coding: utf-8 -*-
from cms.signals.page import pre_save_page, post_save_page, pre_delete_page, post_delete_page, post_moved_page
from cms.signals.permissions import post_save_user, post_save_user_group, pre_save_user, pre_delete_user, pre_save_group, pre_delete_group, pre_save_pagepermission, pre_delete_pagepermission, pre_save_globalpagepermission, pre_delete_globalpagepermission
from cms.signals.placeholder import pre_delete_placeholder_ref, post_delete_placeholder_ref
from cms.signals.plugins import update_plugin_positions
from cms.signals.reversion_signals import post_revision
from cms.signals.title import pre_save_title, post_save_title, pre_delete_title, post_delete_title
from cms.utils.conf import get_cms_setting
from django.db.models import signals
from django.dispatch import Signal

from cms.models import Page, Title, CMSPlugin, PagePermission, GlobalPagePermission, PageUser, PageUserGroup, PlaceholderReference
from django.conf import settings
from django.contrib.auth.models import User, Group

#################### Our own signals ###################

# fired after page location is changed - is moved from one node to other
page_moved = Signal(providing_args=["instance"])

# fired after page gets published - copied to public model - there may be more
# than one instances published before this signal gets called
post_publish = Signal(providing_args=["instance", "language"])
post_unpublish = Signal(providing_args=["instance", "language"])

# fired if a public page with an apphook is added or changed
urls_need_reloading = Signal(providing_args=[])

######################### plugins #######################

signals.post_delete.connect(update_plugin_positions, sender=CMSPlugin)

########################## page #########################

signals.pre_save.connect(pre_save_page, sender=Page)
signals.post_save.connect(post_save_page, sender=Page)
signals.pre_delete.connect(pre_delete_page, sender=Page)
signals.post_delete.connect(post_delete_page, sender=Page)
page_moved.connect(post_moved_page, sender=Page)

######################### title #########################

signals.pre_save.connect(pre_save_title, sender=Title)
signals.post_save.connect(post_save_title, sender=Title)
signals.pre_delete.connect(pre_delete_title, sender=Title)
signals.post_delete.connect(post_delete_title, sender=Title)

###################### placeholder #######################

signals.pre_delete.connect(pre_delete_placeholder_ref, sender=PlaceholderReference)
signals.post_delete.connect(post_delete_placeholder_ref, sender=PlaceholderReference)

###################### permissions #######################

if get_cms_setting('PERMISSION'):
    # only if permissions are in use

    # register signals to user related models
    signals.post_save.connect(post_save_user, User)
    signals.post_save.connect(post_save_user_group, Group)

    signals.pre_save.connect(pre_save_user, sender=User)
    signals.pre_delete.connect(pre_delete_user, sender=User)

    signals.pre_save.connect(pre_save_user, sender=PageUser)
    signals.pre_delete.connect(pre_delete_user, sender=PageUser)

    signals.pre_save.connect(pre_save_group, sender=Group)
    signals.pre_delete.connect(pre_delete_group, sender=Group)

    signals.pre_save.connect(pre_save_group, sender=PageUserGroup)
    signals.pre_delete.connect(pre_delete_group, sender=PageUserGroup)

    signals.pre_save.connect(pre_save_pagepermission, sender=PagePermission)
    signals.pre_delete.connect(pre_delete_pagepermission, sender=PagePermission)

    signals.pre_save.connect(pre_save_globalpagepermission, sender=GlobalPagePermission)
    signals.pre_delete.connect(pre_delete_globalpagepermission, sender=GlobalPagePermission)

if 'reversion' in settings.INSTALLED_APPS:
    from reversion.models import post_revision_commit

    post_revision_commit.connect(post_revision)


from django.db.models import signals
from django.conf import settings
from cms.models import Page, Title
from cms.models import CMSPlugin        
from cms.utils.moderator import page_changed
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import Signal

# fired after page location is changed - is moved from one node to other
page_moved = Signal(providing_args=["instance"])

# fired when some of nodes (Title) with applications gets saved
application_post_changed = Signal(providing_args=["instance"])

# fired after page gets published - copied to public model - there may be more
# than one instances published before this signal gets called
post_publish = Signal(providing_args=["instance"])
        
def update_plugin_positions(**kwargs):
    plugin = kwargs['instance']
    plugins = CMSPlugin.objects.filter(page=plugin.page, language=plugin.language, placeholder=plugin.placeholder).order_by("position")
    last = 0
    for p in plugins:
        if p.position != last:
            p.position = last
            p.save()
        last += 1

signals.post_delete.connect(update_plugin_positions, sender=CMSPlugin, dispatch_uid="cms.plugin.update_position")


def update_title_paths(instance, **kwargs):
    """Update child pages paths in case when page was moved.
    """
    for title in instance.title_set.all():
        title.save()
        
page_moved.connect(update_title_paths, sender=Page, dispatch_uid="cms.title.update_path")


def pre_save_title(instance, raw, **kwargs):
    """Save old state to instance and setup path
    """
    instance.tmp_path = None
    instance.tmp_application_urls = None
    
    if instance.id:
        try:
            tmp_title = Title.objects.get(pk=instance.id)
            instance.tmp_path = tmp_title.path
            instance.tmp_application_urls = tmp_title.application_urls
        except:
            pass # no Titles exist for this page yet
    
    # Build path from parent page's path and slug
    if instance.has_url_overwrite and instance.path:
        instance.path = instance.path.strip(" /")
    else:
        parent_page = instance.page.parent
        slug = u'%s' % instance.slug
        
        instance.path = u'%s' % slug
        if parent_page:
            parent_title = Title.objects.get_title(parent_page, language=instance.language, language_fallback=True)
            if parent_title:
                instance.path = (u'%s/%s' % (parent_title.path, slug)).lstrip("/")
        
signals.pre_save.connect(pre_save_title, sender=Title, dispatch_uid="cms.title.presave")


def post_save_title(instance, raw, created, **kwargs):
    # Update descendants only if path changed
    application_changed = False
    
    if instance.path != getattr(instance,'tmp_path',None) and not hasattr(instance, 'tmp_prevent_descendant_update'):
        descendant_titles = Title.objects.filter(
            page__lft__gt=instance.page.lft, 
            page__rght__lt=instance.page.rght, 
            page__tree_id__exact=instance.page.tree_id,
            language=instance.language
        ).order_by('page__tree_id', 'page__parent', 'page__lft')
        
        for descendant_title in descendant_titles:
            descendant_title.path = '' # just reset path
            descendant_title.tmp_prevent_descendant_update = True
            if descendant_title.application_urls:
                application_changed = True
            descendant_title.save()
        
    if not hasattr(instance, 'tmp_prevent_descendant_update') and \
        (instance.application_urls != getattr(instance, 'tmp_application_urls', None) or application_changed):
        # fire it if we have some application linked to this page or some descendant
        application_post_changed.send(sender=Title, instance=instance)
    
    # remove temporary attributes
    if getattr( instance, 'tmp_path', None):
        del(instance.tmp_path)
    if getattr( instance, 'tmp_application_urls' , None):
        del(instance.tmp_application_urls)
    
    try:
        del(instance.tmp_prevent_descendant_update)
    except AttributeError:
        pass

signals.post_save.connect(post_save_title, sender=Title, dispatch_uid="cms.title.postsave")        


def post_save_user(instance, raw, created, **kwargs):
    """Signal called when new user is created, required only when CMS_PERMISSION.
    Asignes creator of the user to PageUserInfo model, so we now who had created 
    this user account.
    
    requires: CurrentUserMiddleware
    """
    from cms.utils.permissions import get_current_user
    # read current user from thread locals
    creator = get_current_user()
    if not creator or not created or not hasattr(creator, 'pk'):
        return
    
    from cms.models import PageUser
    from django.db import connection
    
    # i'm not sure if there is a workaround for this, somebody any ideas? What
    # we are doing here is creating PageUser on Top of existing user, i'll do it 
    # through plain SQL, its not nice, but...
    
    # TODO: find a better way than an raw sql !!
    
    cursor = connection.cursor()
    query = "INSERT INTO %s (user_ptr_id, created_by_id) VALUES (%d, %d)" % (
        PageUser._meta.db_table,
        instance.pk, 
        creator.pk
    )
    cursor.execute(query) 
    cursor.close()
    
def post_save_user_group(instance, raw, created, **kwargs):
    """The same like post_save_user, but for Group, required only when 
    CMS_PERMISSION.
    Asignes creator of the group to PageUserGroupInfo model, so we now who had
    created this user account.
    
    requires: CurrentUserMiddleware
    """
    from cms.utils.permissions import get_current_user
    # read current user from thread locals
    creator = get_current_user()
    if not creator or not created:
        return
    
    from cms.models import PageUserGroup
    from django.db import connection
    
    # TODO: same as in post_save_user - raw sql is just not nice - workaround...?
    
    cursor = connection.cursor()
    query = "INSERT INTO %s (group_ptr_id, created_by_id) VALUES (%d, %d)" % (
        PageUserGroup._meta.db_table,
        instance.pk, 
        creator.pk
    )
    cursor.execute(query) 
    cursor.close()
    
if settings.CMS_PERMISSION:
    # only if permissions are in use
    from django.contrib.auth.models import User, Group
    # regster signals to user related models
    signals.post_save.connect(post_save_user, User)
    signals.post_save.connect(post_save_user_group, Group)


def pre_save_page(instance, raw, **kwargs):
    """Helper pre save signal, assigns old_page attribute, so we can still
    compare changes. Currently used only if CMS_PUBLISHER
    """
    instance.old_page = None
    try:
        instance.old_page = Page.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        pass
        

def post_save_page(instance, raw, created, **kwargs):   
    """Helper post save signal, cleans old_page attribute.
    """
    old_page = instance.old_page
    del(instance.old_page)
    
    if settings.CMS_MODERATOR:
        # tell moderator something was happen with this page
        page_changed(instance, old_page)
    

if settings.CMS_MODERATOR:
    # tell moderator, there is something happening with this page
    signals.pre_save.connect(pre_save_page, sender=Page, dispatch_uid="cms.page.presave")
    signals.post_save.connect(post_save_page, sender=Page, dispatch_uid="cms.page.postsave")
    
 
from cms.models import PagePermission, GlobalPagePermission
from cms.cache.permissions import clear_user_permission_cache,\
    clear_permission_cache


def pre_save_user(instance, raw, **kwargs):
    clear_user_permission_cache(instance)

def pre_delete_user(instance, **kwargs):
    clear_user_permission_cache(instance)

def pre_save_group(instance, raw, **kwargs):
    if instance.pk:
        for user in instance.user_set.filter(is_staff=True):
            clear_user_permission_cache(user)

def pre_delete_group(instance, **kwargs):
    for user in instance.user_set.filter(is_staff=True):
        clear_user_permission_cache(user)
    
def pre_save_pagepermission(instance, raw, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_delete_pagepermission(instance, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_save_globalpagepermission(instance, raw, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_delete_globalpagepermission(instance, **kwargs):
    if instance.user:
        clear_user_permission_cache(instance.user)

def pre_save_delete_page(instance, **kwargs):
    clear_permission_cache()


if settings.CMS_PERMISSION:
    # TODO: will this work also with PageUser and PageGroup??
    signals.pre_save.connect(pre_save_user, sender=User)
    signals.pre_delete.connect(pre_delete_user, sender=User)
    
    signals.pre_save.connect(pre_save_group, sender=Group)
    signals.pre_delete.connect(pre_delete_group, sender=Group)
    
    signals.pre_save.connect(pre_save_pagepermission, sender=PagePermission)
    signals.pre_delete.connect(pre_delete_pagepermission, sender=PagePermission)
    
    signals.pre_save.connect(pre_save_globalpagepermission, sender=GlobalPagePermission)
    signals.pre_delete.connect(pre_delete_globalpagepermission, sender=GlobalPagePermission)
    
    signals.pre_save.connect(pre_save_delete_page, sender=Page)
    signals.pre_delete.connect(pre_save_delete_page, sender=Page)



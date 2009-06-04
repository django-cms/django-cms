from django.db.models import signals
from cms import settings as cms_settings, appresolver
from cms.models import signals as cms_signals, Page, Title
from cms.models import CMSPlugin        
        
def update_plugin_positions(**kwargs):
    plugin = kwargs['instance']
    plugins = CMSPlugin.objects.filter(page=plugin.page, language=plugin.language, placeholder=plugin.placeholder).order_by("position")
    last = 0
    for p in plugins:
        if p.position != last:
            p.position = last
            p.save()
        last += 1

signals.post_delete.connect(update_plugin_positions, sender=CMSPlugin)


def update_title_paths(instance, **kwargs):
    """Update child pages paths in case when page was moved.
    """
    for title in instance.title_set.all():
        title.save()
        
cms_signals.page_moved.connect(update_title_paths, sender=Page)


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
        if parent_page:
            parent_path = Title.objects.get_title(parent_page, language=instance.language, language_fallback=True).path
            instance.path = (u'%s/%s' % (parent_path, slug)).lstrip("/")
        else:
            instance.path = u'%s' % slug

signals.pre_save.connect(pre_save_title, sender=Title)


def post_save_title(instance, raw, created, **kwargs):
    # Update descendants only if path changed
    application_changed = False
    
    if instance.path != instance.tmp_path and not hasattr(instance, 'tmp_prevent_descendant_update'):
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
        (instance.application_urls != instance.tmp_application_urls or application_changed):
        # fire it if we have some application linked to this page or some descendant
        cms_signals.application_post_changed.send(sender=Title, instance=instance)
    
    # remove temporary attributes
    del(instance.tmp_path)
    del(instance.tmp_application_urls)
    
    try:
        del(instance.tmp_prevent_descendant_update)
    except AttributeError:
        pass

signals.post_save.connect(post_save_title, sender=Title)


def clear_appresolver_cache(instance, **kwargs):
    # reset cached applications - there were a change probably
    appresolver.dynamic_app_regex_url_resolver.reset_cache()


if cms_settings.CMS_APPLICATIONS_URLS:
    # register this signal only if we have some hookable applications
    cms_signals.application_post_changed.connect(clear_appresolver_cache, sender=Title)        



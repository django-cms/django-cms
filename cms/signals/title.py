# -*- coding: utf-8 -*-

from cms.models import Title, Page
from cms.signals.apphook import apphook_pre_title_checker, apphook_post_title_checker, apphook_post_delete_title_checker


def update_title_paths(instance, **kwargs):
    """Update child pages paths in case when page was moved.
    """
    for title in instance.title_set.all():
        title.save()


def update_title(title):
    slug = u'%s' % title.slug
    if title.page.is_home:
        title.path = ''
    elif not title.has_url_overwrite:
        title.path = u'%s' % slug
        parent_page_id = title.page.parent_id
        if parent_page_id:
            parent_title = Title.objects.get_title(parent_page_id,
                                                   language=title.language, language_fallback=True)
            if parent_title:
                title.path = (u'%s/%s' % (parent_title.path, slug)).lstrip("/")


def pre_save_title(instance, raw, **kwargs):
    """Save old state to instance and setup path
    """
    page = instance.page
    page_languages = page.get_languages()

    if not instance.language in page_languages:
        page_languages.append(instance.language)
        page.update_languages(page_languages)

    if instance.pk and not hasattr(instance, "tmp_path"):
        instance.tmp_path = None
        try:
            instance.tmp_path = Title.objects.filter(pk=instance.pk).values_list('path')[0][0]
        except IndexError:
            pass  # no Titles exist for this page yet
    # Build path from parent page's path and slug
    if instance.has_url_overwrite and instance.path:
        instance.path = instance.path.strip(" /")
    else:
        update_title(instance)
    apphook_pre_title_checker(instance, **kwargs)


def post_save_title(instance, raw, created, **kwargs):
    # Update descendants only if path changed
    prevent_descendants = hasattr(instance, 'tmp_prevent_descendant_update')
    if instance.path != getattr(instance, 'tmp_path', None) and not prevent_descendants:
        child_titles = Title.objects.filter(
            page__depth=instance.page.depth + 1,
            page__path__range=Page._get_children_path_interval(instance.page.path),
            language=instance.language,
            has_url_overwrite=False, # TODO: what if child has no url overwrite?
        ).order_by('page__depth', 'page__path')

        for child_title in child_titles:
            child_title.path = ''  # just reset path
            child_title.tmp_prevent_descendant_update = True
            child_title._publisher_keep_state = True
            child_title.save()
            # remove temporary attributes
    if hasattr(instance, 'tmp_path'):
        del instance.tmp_path
    if prevent_descendants:
        del instance.tmp_prevent_descendant_update
    apphook_post_title_checker(instance, **kwargs)


def pre_delete_title(instance, **kwargs):
    """Save old state to instance and setup path
    """
    page = instance.page
    page_languages = page.get_languages()

    if instance.language in page_languages:
        page_languages.remove(instance.language)
        page.update_languages(page_languages)

    if instance.publisher_is_draft:
        instance.page.mark_descendants_pending(instance.language)


def post_delete_title(instance, **kwargs):
    apphook_post_delete_title_checker(instance, **kwargs)

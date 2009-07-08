from cms import settings as cms_settings

APPEND_TO_SLUG = "_copy"

def is_valid_page_slug(page, parent, lang, slug, site):
    """Validates given slug depending on settings.
    """
    from cms.models import Title
    if cms_settings.CMS_UNIQUE_SLUGS:
        titles = Title.objects.filter(slug=slug)
    else:
        titles = Title.objects.filter(slug=slug, language=lang)
    if not cms_settings.CMS_FLAT_URLS:
        if parent and not parent.is_home():
            titles = titles.filter(page__parent=parent)
        else:
            titles = titles.filter(page__parent__isnull=True)
    titles = titles.filter(page__site=site)
    if page.pk:
        titles = titles.exclude(language=lang, page=page)
    if titles.count():
        return False
    return True


def get_available_slug(title, new_slug=None):
    """Smart function generates slug for title if current title slug cannot be
    used. Appends APPEND_TO_SLUG to slug and checks it again.
    
    (Used in page copy function)
    
    Returns: slug
    """
    slug = new_slug or title.slug
    if is_valid_page_slug(title.page, title.page.parent, title.language, slug, title.page.site_id):
        return title.slug
    return get_available_slug(title, title.slug + APPEND_TO_SLUG)
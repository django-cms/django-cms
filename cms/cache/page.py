from django.core.cache import cache

TTL = 600  

PUBLIC_PAGE_PUBLISHED_CACHE_KEY = "Page::Public::Published::Ids"  

def is_public_published(page):
    """Returns True if public model for given page exists and haves published True.
    Cache gets filled up if its empty.
    """
    public_published_page_id_set = cache.get(PUBLIC_PAGE_PUBLISHED_CACHE_KEY)
    
    if not public_published_page_id_set:
        from cms.models import Page
        public_published_page_id_set = Page.PublicModel.objects.filter(published=True).values_list('id', flat=True)
        cache.set(PUBLIC_PAGE_PUBLISHED_CACHE_KEY, list(public_published_page_id_set), TTL)
    
    return page.public_id in public_published_page_id_set


def clear_public_page_cache():
    cache.delete(PUBLIC_PAGE_PUBLISHED_CACHE_KEY)
from cms.models import Page
from django.core.urlresolvers import RegexURLResolver, Resolver404

def resolve_with_applications(request, current_page, path, language):
    """Tries to found if given path should be resolved over application. 
    Applications have higher priority than other cms pages. If there is 
    """
    
    page_set = Page.objects.get_pages_with_application(request.site, path, language)
    
    for page in page_set:
        urlconf_name = page.get_application_urls(language)
        page_path = page.get_path(language)
        resolver = RegexURLResolver(r'^' + page_path + "/", urlconf_name)
        
        try:
            callback, callback_args, callback_kwargs = resolver.resolve(path)
            # application hook found
            response = callback(request, *callback_args, **callback_kwargs)
            return current_page or page, response
        except Resolver404:
            pass
        
    return current_page, None


class DynamicAppRegexUrlResolver(RegexURLResolver):
    """Dynamic application url resolver.
    
    Used for adding support to standard reverse function used by standard 
    applications, so the hookable applications can use it also
    
    Paths in hookable applications are dynamic, so some db lookup is required 
    here.
    """
    def __init__(self):
        super(DynamicAppRegexUrlResolver, self).__init__(r'^/', 'DynamicAppResolver', {})
        
    # fake this and provide dynamic instance instead of module
    urlconf_module = lambda self: dynamic_url_conf_module
        
        
class DynamicUrlConfModule(object):
    """Fake urls module class. Creates resolvers for hookable applications on
    the fly from db. 
    
    Currently only urlpatterns are accessed from url_conf module, so this 
    provides urlpatterns property.
    
    IMPORTANT!: If will be RegexURLResolver changed from django team, this may 
    lead to problems and have to be fixed.
    """
    def __init__(self):
        self._urlpatterns = None
    
    @property
    def urlpatterns(self):
        """Create urlresolvers for hookable applications on the fly.
        
        Caches result, so db lookup is required only once, or when the cache
        is reseted.
        """
        
        if not self._urlpatterns:
            pages = Page.objects.get_all_pages_with_application()
            self._urlpatterns, included = [], []
            
            for page in pages:
                # get all titles with application
                title_set = page.title_set.filter(application_urls__gt="")
                for title in title_set:
                    mixid = "%s:%" % (title.path, title.application_urls)
                    if mixid in included:
                        # don't add the same thing twice
                        continue  
                    self._urlpatterns.append(self._create_resolver(title))
                    included.append(mixid)
        print "> APP Patterns:", self._urlpatterns
        return self._urlpatterns
    
    def _create_resolver(self, title):
        # NOTE: can we use default_kwargs here to pass some aditional data
        # to application? - can we deefine some data in admin and pass them here
        # will they be be than passed to pattern, and from pattern to view? 
        # If it will work, will be give us possibility to configure one
        # application for multiple hooks. 
        regex = r'^%s' % title.path 
        resolver = RegexURLResolver(regex, title.application_urls)
        return resolver
    
    def reset_cache(self):
        """Reset urlpatterns cache. Should be called always when there is some
        application change on any page
        """
        self._urlpatterns = None
        # recache patterns with new state
        fake = self.urlpatterns

dynamic_url_conf_module = DynamicUrlConfModule()
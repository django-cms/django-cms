from django.conf import settings
from cms import settings as cms_settings 
from django.core.urlresolvers import RegexURLResolver, Resolver404, reverse
from cms.utils.moderator import get_page_queryset
from cms.models import Title
from cms.models.pagemodel import Page
from cms.exceptions import NoHomeFound


def applications_page_check(request, current_page=None, path=None):
    """Tries to find if given path was resolved over application. 
    Applications have higher priority than other cms pages. 
    """
    if current_page:
        return current_page
    if path is None:
        path = request.path.replace(reverse('pages-root'), '', 1)
    # check if application resolver can resolve this
    try:
        page_id = dynamic_app_regex_url_resolver.resolve_page_id(path+"/")
        # yes, it is application page
        page = get_page_queryset(request).get(id=page_id)
        # If current page was matched, then we have some override for content
        # from cms, but keep current page. Otherwise return page to which was application assigned.
        return page 
    except Resolver404:
        pass
    return None    

class PageRegexURLResolver(RegexURLResolver):
    page_id = None
    
    def resolve_page_id(self, path):
        """Resolves requested path similar way how resolve does, but instead
        of return callback,.. returns page_id to which was application 
        assigned.
        """
        tried = []
        match = self.regex.search(path)
        if match:
            new_path = path[match.end():]
            for pattern in self.urlconf_module.urlpatterns:
                try:
                    sub_match = pattern.resolve(new_path)
                except Resolver404, e:
                    if 'tried' in e.args[0]:
                        tried.extend([(pattern.regex.pattern + '   ' + t) for t in e.args[0]['tried']])
                    elif 'path' in e.args[0]:
                        tried.extend([(pattern.regex.pattern + '   ' + t) for t in e.args[0]['path']])
                else:
                    if sub_match:
                        if isinstance(pattern, RegexURLResolver):
                            return pattern.page_id
                        else:
                            return self.page_id
                    tried.append(pattern.regex.pattern)
            raise Resolver404, {'tried': tried, 'path': new_path}


class DynamicAppRegexURLResolver(PageRegexURLResolver):
    """Dynamic application url resolver.
    
    Used for adding support to standard reverse function used by standard 
    applications, so the hookable applications can use it also
    
    Paths in hookable applications are dynamic, so some db lookup is required 
    here.
    """
    
    def __init__(self):
        super(DynamicAppRegexURLResolver, self).__init__(r'^', "DynamicAppResolver", {})
        self._dynamic_url_conf_module = DynamicURLConfModule()
        
    # fake this and provide dynamic instance instead of module
    @property
    def urlconf_module(self): 
        return self._dynamic_url_conf_module
    
    def reset_cache(self):
        self._dynamic_url_conf_module.reset_cache()
        from django.core import urlresolvers
        urlresolvers._resolver_cache = {}
            
    

class ApplicationRegexUrlResolver(PageRegexURLResolver):
    def __init__(self, path, title, default_kwargs={}):
        """Creates standard variant of RegexUrlResolver, but adds some usefull
        functionality to it.
        
        Args:
            title: Title instance
            default_kwargs
        """
        
        # NOTE: can we use default_kwargs here to pass some aditional data
        # to application? - can we deefine some data in admin and pass them here
        # will they be be than passed to pattern, and from pattern to view? 
        # If it will work, will be give us possibility to configure one
        # application for multiple hooks. 
        regex = r'^%s' % path    
        if settings.APPEND_SLASH:
            regex += r'/'  
        urlconf_name = title.application_urls
        
        # assign page_id to resolver, so he knows on which page he was assigned
        self.page_id = title.page_id
        super(ApplicationRegexUrlResolver, self).__init__(regex, urlconf_name, default_kwargs)
    
                
class DynamicURLConfModule(object):
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
            # TODO: will this work with multiple sites? how are they exactly
            # implemented ?
            # probably will be better to make caching per site
            
            self._urlpatterns, included = [], []
            # we don't have a request here so get_page_queryset() can't be used,
            # so, if CMS_MODERATOR, use, public() queryset, otherwise 
            # use draft(). This can be done, because url patterns are used just 
            # in frontend
            
            is_draft = not cms_settings.CMS_MODERATOR
            try:
                home = Page.objects.get_home()
                home_titles = home.title_set.all()
            except NoHomeFound:
                home_titles = []
            home_slugs = {}
            for title in home_titles:
                home_slugs[title.language] = title.slug
            title_qs = Title.objects.filter(page__publisher_is_draft=is_draft)
            
            urls = []
            for title in title_qs.filter(application_urls__gt="").select_related():
                if cms_settings.CMS_FLAT_URLS:
                    if title.language in home_slugs:
                        path = title.slug.split(home_slugs[title.language] + "/", 1)[-1]
                    else:
                        path = title.slug
                    mixid = "%s:%s" % (path + "/", title.application_urls)
                else:
                    if title.language in home_slugs:
                        path = title.path.split(home_slugs[title.language] + "/", 1)[-1]
                    else:
                        path = title.path
                    mixid = "%s:%s" % (path + "/", title.application_urls)
                if mixid in included:
                    # don't add the same thing twice
                    continue  
                urls.append(ApplicationRegexUrlResolver(path, title))
                included.append(mixid)
            self._urlpatterns = urls
        return self._urlpatterns
        
    def reset_cache(self):
        """Reset urlpatterns cache. Should be called always when there is some
        application change on any page
        """
        self._urlpatterns = None
        # recache patterns with new state
        #fake = self.urlpatterns        
    
dynamic_app_regex_url_resolver = DynamicAppRegexURLResolver()
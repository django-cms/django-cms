from django.forms.widgets import Media
from django.utils.encoding import smart_unicode
from django.conf import settings
from cms.middleware.toolbar import HTML_TYPES

def inster_before_tag(string, tag, insertion):
    no_case = string.lower()
    index = no_case.find("<%s" % tag.lower())
    if index > -1:
        start_tag = index
        return string[:start_tag] + insertion + string[start_tag:]
    else:
        return string

class PlaceholderMediaMiddleware(object):
    def inject_media(self, request, response):
        if request.is_ajax():
            return False
        if response.status_code != 200:
            return False 
        if not response['Content-Type'].split(';')[0] in HTML_TYPES:
            return False
        if request.path_info.startswith(settings.MEDIA_URL):
            return False
        return True
    
    def process_request(self, request):
        request.placeholder_media = Media()
        
    def process_response(self, request, response):
        if self.inject_media(request, response) and hasattr(request,'placeholder_media'):
            response.content = inster_before_tag(smart_unicode(response.content),
                u'/head', smart_unicode(request.placeholder_media.render()))
        return response

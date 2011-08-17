from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
import os
from django.conf import settings

class File(CMSPlugin):
    """
    Plugin for storing any type of file.
    
    Default template displays download link with icon (if available) and file size.
    
    Icons are searched for within <MEDIA_ROOT>/<CMS_FILE_ICON_PATH> 
    (CMS_FILE_ICON_PATH is a plugin-specific setting which defaults to "<CMS_MEDIA_PATH>/images/file_icons")
    with filenames of the form <file_ext>.<icon_ext>, where <file_ext> is the extension
    of the file itself, and <icon_ext> is one of <CMS_FILE_ICON_EXTENSIONS>
    (another plugin specific setting, which defaults to ('gif', 'png'))
    
    This could be updated to use the mimetypes library to determine the type of file rather than
    storing a separate icon for each different extension.
    
    The icon search is currently performed within get_icon_url; this is probably a performance concern.
    """
    file = models.FileField(_("file"), upload_to=CMSPlugin.get_media_path)
    title = models.CharField(_("title"), max_length=255, null=True, blank=True)
    # CMS_ICON_EXTENSIONS and CMS_ICON_PATH are assumed to be plugin-specific, and not included in cms.settings
    # -- they are therefore imported from django.conf.settings
    ICON_EXTENSIONS = getattr(settings, "CMS_FILE_ICON_EXTENSIONS", ('gif', 'png'))
    ICON_PATH = getattr(settings, "CMS_FILE_ICON_PATH", os.path.join(settings.STATIC_ROOT, "cms", "images", "file_icons"))
    ICON_URL = getattr(settings, "CMS_FILE_ICON_URL", "%s%s/%s/%s/" % (settings.STATIC_URL, "cms", "images", "file_icons"))
        
    def get_icon_url(self):
        path_base = os.path.join(self.ICON_PATH, self.get_ext())
        url_base = '%s%s' % (self.ICON_URL, self.get_ext())
        for ext in self.ICON_EXTENSIONS:
            if os.path.exists("%s.%s" % (path_base, ext)): 
                return "%s.%s" % (url_base, ext)
        return None
        
    def file_exists(self):
        return os.path.exists(self.file.path)
        
    def get_file_name(self):
        return os.path.basename(self.file.path)
        
    def get_ext(self):
        return os.path.splitext(self.get_file_name())[1][1:].lower()
        
    def __unicode__(self):
        if self.title: 
            return self.title;
        elif self.file:
            # added if, because it raised attribute error when file wasnt defined
            return self.get_file_name();
        return "<empty>"

    search_fields = ('title',)

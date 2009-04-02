
from django.db import models
from django.utils.translation import ugettext_lazy as _
from cms.models import CMSPlugin
from os.path import join, basename, splitext, exists
import math

from cms import settings

if 'reversion' in settings.INSTALLED_APPS:
    import reversion

class File(CMSPlugin):
	"""
	Plugin for storing any type of file.
	
	Default template displays download link with icon (if available) and file size.
	
	Icons are searched for within <CMS_MEDIA_ROOT>/<CMS_ICON_PATH> 
	(CMS_ICON_PATH is a plugin-specific setting which defaults to "images/icons")
	with filenames of the form <file_ext>.<icon_ext>, where <file_ext> is the extension
	of the file itself, and <icon_ext> is one of <CMS_ICON_EXTENSIONS>
	(another plugin specific setting, which defaults to ('gif', 'png'))
	
	The search is currently performed within get_icon_url; this is probably a performance
	concern.
	"""
	file = models.FileField(_("file"), upload_to=CMSPlugin.get_media_path)
	title = models.CharField(_("title"), max_length=255, null=True, blank=True)
	ICON_EXTENSIONS = getattr(settings, "CMS_ICON_EXTENSIONS", ('gif', 'png'))
	ICON_PATH = getattr(settings, "CMS_ICON_PATH", join("images", "icons"))
	def get_icon_url(self):
		base = join(self.ICON_PATH, self.get_ext())
		for ext in self.ICON_EXTENSIONS:
			relative = "%s.%s" % (base, ext)
			if exists(join(settings.CMS_MEDIA_ROOT, relative)): 
				return join(settings.CMS_MEDIA_URL, relative)
		return None
	def get_file_name(self):
		return basename(self.file.path)
	def get_ext(self):
		return splitext(self.get_file_name())[1][1:]
	def __unicode__(self):
		if self.title: return self.title;
		return self.get_file_name();

if 'reversion' in settings.INSTALLED_APPS:        
    reversion.register(File, follow=["cmsplugin_ptr"])
    

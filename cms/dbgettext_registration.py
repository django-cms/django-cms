from dbgettext.registry import registry, Options
from models import Page
from django.conf import settings

class PageOptions(Options):
    attributes = ('get_title', 'get_slug')
    translate_if = {'published' : True,}
    def get_path_identifier(self, obj):
        return obj.get_path()

if settings.CMS_MODERATOR:
    PageOptions.translate_if['publisher_is_draft'] = False

registry.register(Page, PageOptions)

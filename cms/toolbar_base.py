from django.forms import MediaDefiningClass

from cms.exceptions import LanguageError
from cms.utils import get_current_site, get_language_from_request
from cms.utils.i18n import get_language_code


class CMSToolbar(metaclass=MediaDefiningClass):
    supported_apps = None

    #: Toolbars are populated in ascending priority order. The CMS chrome that
    #: creates the shared menus (the site and language menus) runs first, so
    #: that container-specific toolbars can add items to menus that already
    #: exist. Leave at 0 unless you must run before or after another toolbar.
    priority = 0

    def __init__(self, request, toolbar, is_current_app, app_path):
        self.request = request
        self.toolbar = toolbar
        self.is_current_app = is_current_app
        self.app_path = app_path
        self.current_site = get_current_site(request)
        try:
            self.current_lang = get_language_code(
                get_language_from_request(self.request), self.current_site.pk
            )
        except LanguageError:
            self.current_lang = None

    def populate(self):
        pass

    def post_template_populate(self):
        pass

    @classmethod
    def check_current_app(cls, key, app_name):
        if cls.supported_apps is None:
            local_apps = ".".join(key.split(".")[:-2]),
        else:
            local_apps = cls.supported_apps
        for local_app in local_apps:
            if app_name and local_app and app_name.startswith(local_app):
                return True
        return False

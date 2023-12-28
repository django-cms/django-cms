try:
    from divio_cli import forms
except ImportError:
    from aldryn_client import forms


class Form(forms.BaseForm):
    def to_settings(self, data, settings):
        settings["ADDON_URLS"].append("djangocms_blog.taggit_urls")
        return settings

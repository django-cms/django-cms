from aldryn_client import forms


class Form(forms.BaseForm):
    def to_settings(self, data, settings):
        # No need to setup django-parler. That is already done in aldryn-django-cms
        settings['MIDDLEWARE_CLASSES'].insert(0, 'aldryn_redirects.middleware.RedirectFallbackMiddleware')
        return settings

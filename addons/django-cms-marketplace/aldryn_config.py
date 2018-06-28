from aldryn_client import forms

DEFAULT_MARKETPLACE_ADDON_BASE_URL = 'https://marketplace.django-cms.org/en/addons/browse/'
DEFAULT_MARKETPLACE_NETWORK_BASE_URL = 'https://marketplace.django-cms.org/en/network/browse/'
DEFAULT_ADDONS_API_URL = 'https://control.aldryn.com/apps/addons-marketplace-data/aldryn.com/'
DEFAULT_ADDONS_API_CACHE_TIMEOUT = 60 * 5
DEFAULT_NETWORK_API_URL = 'https://control.aldryn.com/network/profiles'
DEFAULT_NETWORK_API_CACHE_TIMEOUT = 60 * 5
DEFAULT_NETWORK_REFERENCES_API_URL = 'https://control.aldryn.com/network/references/'
DEFAULT_MARKETPLACE_GOOGLE_MAPS_KEY = ''


class Form(forms.BaseForm):
    marketplace_addon_base_url = forms.CharField(
        'Marketplace Addon Apphook URL',
        required=False,
        initial=DEFAULT_MARKETPLACE_ADDON_BASE_URL,
    )
    marketplace_network_base_url = forms.CharField(
        'Marketplace Network Apphook URL',
        required=False,
        initial=DEFAULT_MARKETPLACE_NETWORK_BASE_URL,
    )
    addons_api_url = forms.CharField(
        'Addons API URL to fetch data',
        required=True,
        initial=DEFAULT_ADDONS_API_URL,
    )
    addons_api_cache_timeout = forms.NumberField(
        'Time to cache results from Addons API in seconds (0 means no cache)',
        required=True,
        min_value=0,
        initial=DEFAULT_ADDONS_API_CACHE_TIMEOUT,
    )
    network_api_url = forms.CharField(
        'Network API URL to fetch data.',
        required=True,
        initial=DEFAULT_NETWORK_API_URL,
    )
    network_api_cache_timeout = forms.NumberField(
        'Time to cache results from Network API in seconds (0 means no cache)',
        required=True,
        min_value=0,
        initial=DEFAULT_NETWORK_API_CACHE_TIMEOUT,
    )
    network_references_api_url = forms.CharField(
        'Network References API URL to fetch data.',
        required=True,
        initial=DEFAULT_NETWORK_REFERENCES_API_URL,
    )

    marketplace_google_maps_key = forms.CharField(
        'Marketplace Google Maps key.',
        required=False,
        initial=DEFAULT_MARKETPLACE_GOOGLE_MAPS_KEY,
    )

    mapping = (
        ('DJANGO_CMS_MARKETPLACE_ADDON_BASE_URL', 'marketplace_addon_base_url', DEFAULT_MARKETPLACE_ADDON_BASE_URL),
        ('DJANGO_CMS_MARKETPLACE_NETWORK_BASE_URL', 'marketplace_network_base_url', DEFAULT_MARKETPLACE_NETWORK_BASE_URL),
        ('DJANGO_CMS_MARKETPLACE_ADDONS_API_URL', 'addons_api_url', DEFAULT_ADDONS_API_URL),
        ('DJANGO_CMS_MARKETPLACE_ADDONS_API_CACHE_TIMEOUT', 'addons_api_cache_timeout', DEFAULT_ADDONS_API_CACHE_TIMEOUT),
        ('DJANGO_CMS_MARKETPLACE_NETWORK_API_URL', 'network_api_url', DEFAULT_NETWORK_API_URL),
        ('DJANGO_CMS_MARKETPLACE_NETWORK_API_CACHE_TIMEOUT', 'network_api_cache_timeout', DEFAULT_NETWORK_API_CACHE_TIMEOUT),
        ('DJANGO_CMS_MARKETPLACE_NETWORK_REFERENCES_API_URL', 'network_references_api_url', DEFAULT_NETWORK_REFERENCES_API_URL),
        ('DJANGO_CMS_MARKETPLACE_GOOGLE_MAPS_KEY', 'marketplace_google_maps_key', DEFAULT_MARKETPLACE_GOOGLE_MAPS_KEY),
    )

    def to_settings(self, data, settings):
        for settings_key, value, default in self.mapping:
            settings[settings_key] = data.get(value, default)

        settings['TEMPLATES'][0]['OPTIONS']['context_processors'].append('django_cms_marketplace.context_processors.google_maps_key')
        return settings

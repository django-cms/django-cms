from datetime import datetime, timedelta

from django.utils import timezone

from cms.plugin_base import CMSPluginBase


class NoCachePlugin(CMSPluginBase):
    name = 'NoCache'
    module = 'Test'
    render_plugin = True
    cache = False
    render_template = "plugins/nocache.html"

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context


class LegacyCachePlugin(CMSPluginBase):
    name = 'NoCache'
    module = 'Test'
    render_plugin = True
    # NOTE: We have both the old mechanism...
    cache = False
    render_template = "plugins/nocache.html"

    # And the new...
    def get_cache_expiration(self, request, instance, placeholder):
        """Content is only valid until for 30 seconds."""
        return 30

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context


class TTLCacheExpirationPlugin(CMSPluginBase):
    name = 'TTLCacheExpiration'
    module = 'Test'
    render_plugin = True
    render_template = "plugins/nocache.html"

    def get_cache_expiration(self, request, instance, placeholder):
        """Content is only valid for the next 50 seconds."""
        return 50

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context


class TimeDeltaCacheExpirationPlugin(CMSPluginBase):
    name = 'DateTimeCacheExpiration'
    module = 'Test'
    render_plugin = True
    render_template = "plugins/nocache.html"

    def get_cache_expiration(self, request, instance, placeholder):
        """Content is only valid for the next 45 seconds."""
        return timedelta(seconds=45)

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context


class DateTimeCacheExpirationPlugin(CMSPluginBase):
    name = 'DateTimeCacheExpiration'
    module = 'Test'
    render_plugin = True
    render_template = "plugins/nocache.html"

    def get_cache_expiration(self, request, instance, placeholder):
        """Content is only valid until 40 seconds from now."""
        now = timezone.now()
        return now + timedelta(seconds=40)

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context


class VaryCacheOnPlugin(CMSPluginBase):
    name = 'DateTimeCacheExpiration'
    module = 'Test'
    render_plugin = True
    render_template = "plugins/nocache.html"

    def get_vary_cache_on(self, request, instance, placeholder):
        return ['country-code', ]

    def render(self, context, instance, placeholder):
        request = context.get('request')
        country_code = request.headers.get('Country-Code') or "any"
        context['now'] = country_code
        return context


class SekizaiPlugin(CMSPluginBase):
    name = 'WITH SEki'
    module = 'Test'
    render_plugin = True
    render_template = "plugins/sekizai.html"

    def render(self, context, instance, placeholder):
        context['now'] = datetime.now().microsecond
        return context

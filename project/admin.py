from django.contrib import admin, messages
from django.conf.urls import url
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, get_object_or_404

from . import models


@admin.register(models.PandadocAuthentication)
class PandadocAuthenticationAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'client_id',
        'scope',
    )

    readonly_fields = (
        'access_token',
        'refresh_token',
        'token_expiration',
    )

    def refresh_authorization(modeladmin, request, queryset):
        for each in queryset:
            success, message = each.refresh_authorization()
            if success:
                messages.success(request, '{} successfully refreshed'.format(each))
            else:
                messages.error(request, '{} error: {}'.format(each, message))
    refresh_authorization.short_description = "Refresh authorization for selected authentications"

    actions = (
        refresh_authorization,
    )

    def get_token_for_authorization(self, request, *args, **kwargs):
        """Exchange the OAuth authorization with an access and refresh token"""
        token = request.POST.get('authorization')
        auth = get_object_or_404(models.PandadocAuthentication, id=kwargs['id'])
        success, message = auth.apply_authorization(token)
        if success:
            messages.success(request, 'Access and refresh token successfully updated!')
        else:
            messages.warning(request, message)
        return redirect(reverse('admin:project_pandadocauthentication_change', args=(auth.pk,)))

    def get_urls(self):
        urls = super(PandadocAuthenticationAdmin, self).get_urls()
        return [
            url(r'^(?P<id>[0-9]+)/get-token/$', admin.site.admin_view(self.get_token_for_authorization), name='pandadoc-token'),
        ] + urls

from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin

from .models import FancyPoll


class FancyPollAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass


admin.site.register(FancyPoll, FancyPollAdmin)

from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin

from .models import FancyPoll


@admin.register(FancyPoll)
class FancyPollAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass



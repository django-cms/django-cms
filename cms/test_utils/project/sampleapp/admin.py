from django.contrib import admin

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.admin.utils import GrouperModelAdmin
from cms.test_utils.project.sampleapp.forms import GrouperAdminForm
from cms.test_utils.project.sampleapp.models import (
    Category, GrouperModel, Picture, SampleAppConfig, SomeEditableModel,
)
from cms.utils import get_language_from_request


class PictureInline(admin.StackedInline):
    model = Picture


class CategoryAdmin(admin.ModelAdmin):
    inlines = [PictureInline]


class SomeEditableAdmin(FrontendEditableAdminMixin, admin.ModelAdmin):
    pass


class GrouperAdmin(GrouperModelAdmin):
    form = GrouperAdminForm
    extra_grouping_fields = ("language",)

    def get_list_display(self, request):
        def get_grouper_name(obj):
            language = get_language_from_request(request)
            content = obj.contentmodel_set.filter(language=language).first()
            content = content.secret_greeting if content else "Empty content"
            return f"{obj.category_name}: {content}"

        return (get_grouper_name, )


admin.site.register(Category, CategoryAdmin)
admin.site.register(SampleAppConfig)
admin.site.register(SomeEditableModel, SomeEditableAdmin)
admin.site.register(GrouperModel, GrouperAdmin)


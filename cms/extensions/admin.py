from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse

from cms.extensions import services as extension_services
from cms.models import Page, PageContent
from cms.shared.operations import OperationContext
from cms.utils.urlutils import static_with_version


class ExtensionAdmin(admin.ModelAdmin):
    change_form_template = "admin/cms/extensions/change_form.html"
    add_form_template = "admin/cms/extensions/change_form.html"

    class Media:
        css = {"all": (static_with_version("cms/css/cms.admin.css"),)}

    def save_model(self, request, obj, form, change):
        # The service checks that the user may change what the extension extends.
        extension_services.save_extension(obj, context=OperationContext.from_request(request))

    def delete_model(self, request, obj):
        extension_services.delete_extension(obj, context=OperationContext.from_request(request))

    def delete_queryset(self, request, queryset):
        context = OperationContext.from_request(request)
        with transaction.atomic():
            for extension in queryset:
                extension_services.delete_extension(extension, context=context)


class PageExtensionAdmin(ExtensionAdmin):

    def save_model(self, request, obj, form, change):
        if not change and 'extended_object' in request.GET:
            obj.extended_object = Page.objects.get(pk=request.GET['extended_object'])
        super().save_model(request, obj, form, change)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

    @csrf_protect_m
    def add_view(self, request, form_url='', extra_context=None):
        """
        Check if the page already has an extension object. If so, redirect to edit view instead.
        """
        extended_object_id = request.GET.get('extended_object', False)
        if extended_object_id:
            try:
                page = Page.objects.get(pk=extended_object_id)
                extension = self.model.objects.get(extended_object=page)
                opts = self.model._meta
                change_url = reverse(
                    f'admin:{opts.app_label}_{opts.model_name}_change',
                    args=(extension.pk,),
                    current_app=self.admin_site.name
                )
                return HttpResponseRedirect(change_url)
            except self.model.DoesNotExist:
                pass
        return super().add_view(request, form_url, extra_context)


class PageContentExtensionAdmin(ExtensionAdmin):

    def save_model(self, request, obj, form, change):
        if not change and 'extended_object' in request.GET:
            obj.extended_object = PageContent.admin_manager.get(pk=request.GET['extended_object'])
        super().save_model(request, obj, form, change)

    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}

    @csrf_protect_m
    def add_view(self, request, form_url='', extra_context=None):
        """
        Check if the page already has an extension object. If so, redirect to edit view instead.
        """
        extended_object_id = request.GET.get('extended_object', False)
        if extended_object_id:
            try:
                content = PageContent.admin_manager.get(pk=extended_object_id)
                extension = self.model.objects.get(extended_object=content)
                opts = self.model._meta
                change_url = reverse(
                    f'admin:{opts.app_label}_{opts.model_name}_change',
                    args=(extension.pk,),
                    current_app=self.admin_site.name
                )
                return HttpResponseRedirect(change_url)
            except self.model.DoesNotExist:
                pass
        return super().add_view(request, form_url, extra_context)

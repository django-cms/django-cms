from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse

from cms.models import Page, PageContent
from cms.utils.page_permissions import user_can_change_page


class ExtensionAdmin(admin.ModelAdmin):
    change_form_template = "admin/cms/extensions/change_form.html"
    add_form_template = "admin/cms/extensions/change_form.html"


class PageExtensionAdmin(ExtensionAdmin):

    def save_model(self, request, obj, form, change):
        if not change and 'extended_object' in request.GET:
            obj.extended_object = Page.objects.get(pk=request.GET['extended_object'])
            page = Page.objects.get(pk=request.GET['extended_object'])
        else:
            page = obj.extended_object
        if not user_can_change_page(request.user, page):
            raise PermissionDenied()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if not obj.extended_object.has_change_permission(request.user):
            raise PermissionDenied()
        obj.delete()

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
            content = PageContent.admin_manager.get(pk=request.GET['extended_object'])
        else:
            content = obj.extended_object
        if not user_can_change_page(request.user, page=content.page):
            raise PermissionDenied()
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        page = obj.extended_object.page

        if not user_can_change_page(request.user, page):
            raise PermissionDenied()
        obj.delete()

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

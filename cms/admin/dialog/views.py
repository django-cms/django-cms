# -*- coding: utf-8 -*-
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from cms.models import Page
from cms.utils import get_cms_setting

from cms.admin.dialog.forms import PermissionForm


@staff_member_required
def get_copy_dialog(request, page_id):
    if not get_cms_setting('PERMISSION'):
        return HttpResponse('')

    target_id = request.GET.get('target', False) or request.POST.get('target', False)
    callback = request.GET.get('callback', False) or request.POST.get('callback', False)
    page = get_object_or_404(Page, pk=page_id)
    if target_id:
        target = get_object_or_404(Page, pk=target_id)

    if not page.has_change_permission(request) or (
                target_id and not target.has_add_permission(request)):
        raise Http404

    context = {
        'dialog_id': 'dialog-copy',
        'form': PermissionForm(),  # class needs to be instantiated
        'callback': callback,
    }

    return render(request, "admin/cms/page/tree/copy_premissions.html", context)

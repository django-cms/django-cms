# -*- coding: utf-8 -*-
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response

from cms.models import Page
from cms.utils import get_cms_setting

from cms.admin.dialog.forms import PermissionForm


@staff_member_required
def get_copy_dialog(request, page_id):
    if not get_cms_setting('PERMISSION'):
        return HttpResponse('')

    page = get_object_or_404(Page, pk=page_id)
    target = get_object_or_404(Page, pk=request.REQUEST['target'])

    if not page.has_change_permission(request) or \
            not target.has_add_permission(request):
        raise Http404

    context = {
        'dialog_id': 'dialog-copy',
        'form': PermissionForm(),  # class needs to be instantiated
        'callback': request.REQUEST['callback'],
    }

    return render_to_response("admin/cms/page/tree/copy_premissions.html", context)

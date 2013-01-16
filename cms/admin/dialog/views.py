# -*- coding: utf-8 -*-
from cms.admin.dialog.forms import PermissionForm
from cms.models import Page
from cms.utils import get_cms_setting
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404

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
        'form': PermissionForm(), # class needs to be instantiated
        'callback': request.REQUEST['callback'],
    }
    return render_to_response("admin/cms/page/dialog/copy.html", context)

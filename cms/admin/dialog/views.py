# -*- coding: utf-8 -*-
from cms.admin.dialog.forms import PermissionAndModeratorForm, PermissionForm, ModeratorForm
from cms.models import Page
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404

def _form_class_selector():
    '''
    This replaces the magic that used to happen in forms, where a dynamic 
    class was generated at runtime. Now it's a bit cleaner...
    '''
    form_class = None
    if settings.CMS_PERMISSION and settings.CMS_MODERATOR:
        form_class = PermissionAndModeratorForm
    elif settings.CMS_PERMISSION:
        form_class = PermissionForm
    elif settings.CMS_MODERATOR:
        form_class = ModeratorForm
    return form_class

@staff_member_required
def get_copy_dialog(request, page_id):
    if not (settings.CMS_PERMISSION or settings.CMS_MODERATOR):
        return HttpResponse('')
     
    page = get_object_or_404(Page, pk=page_id)
    target = get_object_or_404(Page, pk=request.REQUEST['target'])
    
    if not page.has_change_permission(request) or \
            not target.has_add_permission(request): # pragma: no cover
        raise Http404 
    
    context = {
        'dialog_id': 'dialog-copy',
        'form': _form_class_selector()(), # class needs to be instanciated
        'callback': request.REQUEST['callback'],
    }
    return render_to_response("admin/cms/page/dialog/copy.html", context)

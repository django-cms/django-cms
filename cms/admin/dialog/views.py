from cms.admin.dialog.forms import get_copy_dialog_form
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse
from django.conf import settings
from cms.models import Page

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
        'form': get_copy_dialog_form(request)(),
        'callback': request.REQUEST['callback'],
    }
    return render_to_response("admin/cms/page/dialog/copy.html", context)

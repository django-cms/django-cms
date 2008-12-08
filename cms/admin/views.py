from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required

from cms import settings
from cms.models import Page, Content, Title

from cms.utils import auto_render
from cms.admin.utils import get_placeholders

def change_status(request, page_id):
    """
    Switch the status of a page
    """
    if request.method == 'POST':
        page = Page.objects.get(pk=page_id)
        if page.status == Page.DRAFT:
            page.status = Page.PUBLISHED
            page.save()
        elif page.status == Page.PUBLISHED:
            page.status = Page.DRAFT
            page.save()
        return HttpResponse(unicode(page.status))
    raise Http404
change_status = staff_member_required(change_status)


def change_innavigation(request, page_id):
    """
    Switch the in_navigation of a page
    """
    if request.method == 'POST':
        page = Page.objects.get(pk=page_id)
        if page.in_navigation:
            page.in_navigation = False
            val = 0
        else:
            page.in_navigation = True
            val = 1
        page.save()
        return HttpResponse(unicode(val))
    raise Http404
change_status = staff_member_required(change_status)

def modify_content(request, page_id, content_id, language_id):
    if request.method == 'POST':
        content = request.POST.get('content', False)
        if not content:
            raise Http404
        page = Page.objects.get(pk=page_id)
        #if settings.CMS_CONTENT_REVISION: #TODO: implement with revisions
        #    Content.objects.create_content_if_changed(page, language_id,
        #                                              content_id, content)
        #else:
        if content_id.lower() not in ['title', 'slug']:
            Content.objects.set_or_create_content(page, language_id,
                                                  content_id, content)
        else:
            if content_id.lower() == "title":
                Title.objects.set_or_create(page, language_id, slug=None, title=content)
            elif content_id.lower() == "slug":
                Title.objects.set_or_create(page, language_id, slug=content, title=None)
        return HttpResponse('ok')
    raise Http404
modify_content = staff_member_required(modify_content)

def traduction(request, page_id, language_id):
    page = Page.objects.get(pk=page_id)
    context = {}
    lang = language_id
    placeholders = get_placeholders(request, page.get_template())
    if Content.objects.get_content(page, language_id, "title") is None:
        language_error = True
    return 'pages/traduction_helper.html', locals()
traduction = staff_member_required(traduction)
traduction = auto_render(traduction)

def get_content(request, page_id, content_id):
    content_instance = get_object_or_404(Content, pk=content_id)
    return HttpResponse(content_instance.body)
get_content = staff_member_required(get_content)
get_content = auto_render(get_content)

def valid_targets_list(request, page_id):
    """A list of valid targets to move a page"""
    if not settings.CMS_PERMISSION:
        perms = "All"
    else:
        from cms.models import PagePermission
        perms = PagePermission.objects.get_page_id_list(request.user)
    query = Page.objects.valid_targets(page_id, request, perms)
    return HttpResponse(",".join([str(p.id) for p in query]))
valid_targets_list = staff_member_required(valid_targets_list)

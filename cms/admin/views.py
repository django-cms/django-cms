from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required

from cms import settings
from cms.models import Page, Title, CMSPlugin

from cms.utils import auto_render
from cms.plugin_pool import plugin_pool
from django.template.context import RequestContext
#from cms.admin.utils import get_placeholders

def change_status(request, page_id):
    """
    Switch the status of a page
    """
    if request.method == 'POST':
        page = Page.objects.get(pk=page_id)
        if page.has_publish_permission(request):
            if page.status == Page.DRAFT:
                page.status = Page.PUBLISHED
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
        if page.has_page_permission(request):
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
        if not page.has_page_permission(request):
            raise Http404
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

#def traduction(request, page_id, language_id):
#    page = Page.objects.get(pk=page_id)
#    context = {}
#    lang = language_id
#    placeholders = get_placeholders(request, page.get_template())
#    if Content.objects.get_content(page, language_id, "title") is None:
#        language_error = True
#    return 'pages/traduction_helper.html', locals()
#traduction = staff_member_required(traduction)
#traduction = auto_render(traduction)

def get_content(request, page_id, content_id):
    content_instance = get_object_or_404(Content, pk=content_id)
    return HttpResponse(content_instance.body)
get_content = staff_member_required(get_content)
get_content = auto_render(get_content)

#def valid_targets_list(request, page_id):
#    """A list of valid targets to move a page"""
#    if not settings.CMS_PERMISSION:
#        perms = "All"
#    else:
#        from cms.models import PagePermission
#        perms = PagePermission.objects.get_edit_id_list(request.user)
#    query = Page.objects.valid_targets(page_id, request, perms)
#    return HttpResponse(",".join([str(p.id) for p in query]))
#valid_targets_list = staff_member_required(valid_targets_list)


def add_plugin(request):
    if request.method == "POST":
        print "add plugin"
        page_id = request.POST['page_id']
        page = get_object_or_404(Page, pk=page_id)
        placeholder = request.POST['placeholder']
        plugin_type = request.POST['plugin_type']
        language = request.POST['language']
        position = CMSPlugin.objects.filter(page=page, language=language, placeholder=placeholder).count()
        plugin = CMSPlugin(page=page, language=language, plugin_type=plugin_type, position=position, placeholder=placeholder) 
        plugin.save()
        request.method = "GET"      
        return edit_plugin(request, plugin.pk)
    raise Http404
    

def remove_plugin(request, plugin_id):
    pass

def edit_plugin(request, plugin_id):
    print plugin_id
    cms_plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
    
    plugin_class = plugin_pool.get_plugin(cms_plugin.plugin_type)()
    model = plugin_class.model
    try:
        instance = model.objects.get(pk=cms_plugin.pk)
    except:
        instance = None
    
    if request.method == "POST":
        if instance:
            form = plugin_class.form(request.POST, request.FILES, instance=instance)
        else:
            form = plugin_class.form(request.POST, request.FILES)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.page = cms_plugin.page
            inst.position = cms_plugin.position
            inst.placeholder = cms_plugin.placeholder
            inst.language = cms_plugin.language
            inst.save()
            return render_to_response('admin/cms/page/plugin_forms_ok.html',{},RequestContext(request))
    else:
        if instance:
            form = plugin_class.form(instance=instance)
        else:
            form = plugin_class.form() 
    return render_to_response('admin/cms/page/plugin_forms.html',{'form':form, 'plugin':cms_plugin}, RequestContext(request))

    
def move_plugin(request, plugin_id , old_position, new_position):
    pass

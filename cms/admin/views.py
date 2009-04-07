from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _
from django.template.context import RequestContext

from cms import settings
from cms.models import Page, Title, CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import auto_render

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

if 'reversion' in settings.INSTALLED_APPS:
    from reversion import revision    

def add_plugin(request):
    if 'history' in request.path or 'recover' in request.path:
        return HttpResponse(str("error"))
    if request.method == "POST":
        page_id = request.POST['page_id']
        page = get_object_or_404(Page, pk=page_id)
        placeholder = request.POST['placeholder'].lower()
        plugin_type = request.POST['plugin_type']
        language = request.POST['language']
        position = CMSPlugin.objects.filter(page=page, language=language, placeholder=placeholder).count()
        plugin = CMSPlugin(page=page, language=language, plugin_type=plugin_type, position=position, placeholder=placeholder) 
        plugin.save()
        if 'reversion' in settings.INSTALLED_APPS:
            page.save()
            save_all_plugins(page)
            revision.user = request.user
            plugin_name = unicode(plugin_pool.get_plugin(plugin_type).name)
            revision.comment = _(u"%(plugin_name)s plugin added to %(placeholder)s") % {'plugin_name':plugin_name, 'placeholder':placeholder}       
        return HttpResponse(str(plugin.pk))
    raise Http404

if 'reversion' in settings.INSTALLED_APPS:
    add_plugin = revision.create_on_success(add_plugin)

def edit_plugin(request, plugin_id):
    if not 'history' in request.path:
        cms_plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        instance, plugin_class = cms_plugin.get_plugin_instance()
    else:
        plugin_id = int(plugin_id)
        from reversion.models import Version
        version_id = request.path.split("/edit-plugin/")[0].split("/")[-1]
        version = get_object_or_404(Version, pk=version_id)
        revs = [related_version.object_version for related_version in version.revision.version_set.all()]
        for rev in revs:
            obj = rev.object
            if obj.__class__ == CMSPlugin and obj.pk == plugin_id:
                cms_plugin = obj
                break
        inst, plugin_class = cms_plugin.get_plugin_instance()
        instance = None
        for rev in revs:
            obj = rev.object
            if obj.__class__ == inst.__class__ and int(obj.pk) == plugin_id:
                instance = obj
                break
    if request.method == "POST":
        if not instance:
            instance = plugin_class.model()    
        instance.pk = cms_plugin.pk
        instance.page = cms_plugin.page
        instance.position = cms_plugin.position
        instance.placeholder = cms_plugin.placeholder
        instance.language = cms_plugin.language
        instance.plugin_type = cms_plugin.plugin_type
        form = plugin_class.form(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            if 'history' in request.path:
                return render_to_response('admin/cms/page/plugin_forms_history.html', {'CMS_MEDIA_URL':settings.CMS_MEDIA_URL, 'is_popup':True},RequestContext(request))
            inst = form.save()
            inst.page.save()
            if 'reversion' in settings.INSTALLED_APPS:
                save_all_plugins(inst.page, [inst.pk])
                revision.user = request.user
                plugin_name = unicode(plugin_pool.get_plugin(inst.plugin_type).name)
                revision.comment = _(u"%(plugin_name)s plugin edited at position %(position)s in %(placeholder)s") % {'plugin_name':plugin_name, 'position':inst.position, 'placeholder':inst.placeholder}
            return render_to_response('admin/cms/page/plugin_forms_ok.html',{'CMS_MEDIA_URL':settings.CMS_MEDIA_URL, 'plugin':cms_plugin, 'is_popup':True, 'name':unicode(inst), "type":inst.get_plugin_name()}, RequestContext(request))
    else:
        if instance:
            form = plugin_class.form(instance=instance)
        else:
            form = plugin_class.form() 
    if plugin_class.form_template:
        template = plugin_class.form_template
    else:
        template = 'admin/cms/page/plugin_forms.html'
    return render_to_response(template, {'form':form, 'plugin':cms_plugin, 'instance':instance, 'is_popup':True, 'CMS_MEDIA_URL':settings.CMS_MEDIA_URL}, RequestContext(request))

if 'reversion' in settings.INSTALLED_APPS:
    edit_plugin = revision.create_on_success(edit_plugin)

def move_plugin(request):
    if request.method == "POST" and not 'history' in request.path:
        pos = 0
        page = None
        for id in request.POST['ids'].split("_"):
            plugin = CMSPlugin.objects.get(pk=id)
            if not page:
                page = plugin.page
            if plugin.position != pos:
                plugin.position = pos
                plugin.save()
            pos += 1
        if page and 'reversion' in settings.INSTALLED_APPS:
            page.save()
            save_all_plugins(page)
            revision.user = request.user
            revision.comment = unicode(_(u"Plugins where moved")) 
        return HttpResponse(str("ok"))
    else:
        raise Http404
    
if 'reversion' in settings.INSTALLED_APPS:
    move_plugin = revision.create_on_success(move_plugin)
  
def remove_plugin(request):
    if request.method == "POST" and not 'history' in request.path:
        plugin_id = request.POST['plugin_id']
        plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        page = plugin.page
        plugin.delete()
        if 'reversion' in settings.INSTALLED_APPS:
            save_all_plugins(page)
            page.save()
            revision.user = request.user
            plugin_name = unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
            revision.comment = _(u"%(plugin_name)s plugin at position %(position)s in %(placeholder)s was deleted.") % {'plugin_name':plugin_name, 'position':plugin.position, 'placeholder':plugin.placeholder}
        return HttpResponse(str(plugin_id))
    raise Http404

if 'reversion' in settings.INSTALLED_APPS:
    remove_plugin = revision.create_on_success(remove_plugin)
    
def save_all_plugins(page, excludes=None):
    for plugin in CMSPlugin.objects.filter(page=page):
        if excludes:
            if plugin.pk in excludes:
                continue
        plugin.save()
        
def revert_plugins(request, version_id):
    from reversion.models import Version
    version = get_object_or_404(Version, pk=version_id)
    revs = [related_version.object_version for related_version in version.revision.version_set.all()]
    plugin_list = []
    titles = []
    page = None
    for rev in revs:
        obj = rev.object
        if obj.__class__ == CMSPlugin:
            plugin_list.append(rev.object)
        if obj.__class__ == Page:
            page = obj
            obj.save()
        if obj.__class__ == Title:
            titles.append(obj) 
    current_plugins = list(CMSPlugin.objects.filter(page=page))
    for plugin in plugin_list:
        plugin.page = page
        plugin.save()
        for old in current_plugins:
            if old.pk == plugin.pk:
                current_plugins.remove(old)
    for title in titles:
        title.page = page
        try:
            title.save()
        except:
            title.pk = Title.objects.get(page=page, language=title.language).pk
            title.save()
    for plugin in current_plugins:
        plugin.delete()
    

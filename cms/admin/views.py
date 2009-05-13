from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.translation import ugettext_lazy as _
from django.template.context import RequestContext

from cms import settings
from cms.models import Page, Title, CMSPlugin
from cms.plugin_pool import plugin_pool
from cms.utils import auto_render
from django.template.defaultfilters import escapejs, force_escape

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
        plugin_type = request.POST['plugin_type']
        page_id = request.POST.get('page_id', None)
        parent = None
        if page_id:
            page = get_object_or_404(Page, pk=page_id)
            placeholder = request.POST['placeholder'].lower()
            language = request.POST['language']
            position = CMSPlugin.objects.filter(page=page, language=language, placeholder=placeholder).count()
        else:
            parent_id = request.POST['parent_id']
            parent = get_object_or_404(CMSPlugin, pk=parent_id)
            page = parent.page
            placeholder = parent.placeholder
            language = parent.language
            position = None
        plugin = CMSPlugin(page=page, language=language, plugin_type=plugin_type, position=position, placeholder=placeholder)
        if parent:
            plugin.parent = parent
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

def edit_plugin(request, plugin_id, admin_site):
    plugin_id = int(plugin_id)
    if not 'history' in request.path:
        cms_plugin = get_object_or_404(CMSPlugin, pk=plugin_id)
        instance, admin = cms_plugin.get_plugin_instance(admin_site)
    else:
        # history view with reversion
        from reversion.models import Version
        version_id = request.path.split("/edit-plugin/")[0].split("/")[-1]
        version = get_object_or_404(Version, pk=version_id)
        revs = [related_version.object_version for related_version in version.revision.version_set.all()]
        
        for rev in revs:
            obj = rev.object
            if obj.__class__ == CMSPlugin and obj.pk == plugin_id:
                cms_plugin = obj
                break
        inst, admin = cms_plugin.get_plugin_instance(admin_site)
        instance = None
        
        for rev in revs:
            obj = rev.object
            if obj.__class__ == inst.__class__ and int(obj.pk) == plugin_id:
                instance = obj
                break
        if not instance:
            # TODO: this should be changed, and render something else.. There
            # can be case when plugin is not using (registered) with reversion
            # so it doesn't haves any version - it should just render plugin
            # and say something like - not in version system..
            raise Http404
        
    # assign required variables to admin
    admin.cms_plugin_instance = cms_plugin
    admin.placeholder = cms_plugin.placeholder # TODO: what for reversion..? should it be inst ...?
    
    if request.method == "POST":
        # set the continue flag, otherwise will admin make redirect to list
        # view, which actually does'nt exists
        request.POST['_continue'] = True
    
    if 'reversion' in settings.INSTALLED_APPS and 'history' in request.path:
        # in case of looking to history just render the plugin content
        context = RequestContext(request)
        return render_to_response(admin.render_template, admin.render(context, instance, admin.placeholder), context)
    
    
    if not instance:
        # instance doesn't exist, call add view
        response = admin.add_view(request)
 
    else:
        # already saved before, call change view
        # we actually have the instance here, but since i won't override
        # change_view method, is better if it will be loaded again, so
        # just pass id to admin
        response = admin.change_view(request, str(plugin_id))
    
    if request.method == "POST" and admin.object_successfully_changed:
        # if reversion is installed, save version of the page plugins
        if 'reversion' in settings.INSTALLED_APPS:
            # perform this only if object was successfully changed
            cms_plugin.page.save()
            save_all_plugins(cms_plugin.page, [cms_plugin.pk])
            revision.user = request.user
            plugin_name = unicode(plugin_pool.get_plugin(cms_plugin.plugin_type).name)
            revision.comment = _(u"%(plugin_name)s plugin edited at position %(position)s in %(placeholder)s") % {'plugin_name':plugin_name, 'position':cms_plugin.position, 'placeholder': cms_plugin.placeholder}
            
        # read the saved object from admin - ugly but works
        saved_object = admin.saved_object
        
        context = {
            'CMS_MEDIA_URL': settings.CMS_MEDIA_URL,
            'plugin': saved_object,
            'is_popup': True,
            'name': unicode(saved_object),
            "type": saved_object.get_plugin_name(),
            'plugin_id': plugin_id,
            'icon': force_escape(escapejs(saved_object.get_instance_icon_src())),
            'alt': force_escape(escapejs(saved_object.get_instance_icon_alt())),
        }
        return render_to_response('admin/cms/page/plugin_forms_ok.html', context, RequestContext(request))
        
    return response

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
        plugin_name = unicode(plugin_pool.get_plugin(plugin.plugin_type).name)
        comment = _(u"%(plugin_name)s plugin at position %(position)s in %(placeholder)s was deleted.") % {'plugin_name':plugin_name, 'position':plugin.position, 'placeholder':plugin.placeholder}
        if 'reversion' in settings.INSTALLED_APPS:
            save_all_plugins(page)
            page.save()
            revision.user = request.user
            revision.comment = comment
        return HttpResponse("%s,%s" % (plugin_id, comment))
    raise Http404

if 'reversion' in settings.INSTALLED_APPS:
    remove_plugin = revision.create_on_success(remove_plugin)
    
def save_all_plugins(page, excludes=None):
    for plugin in CMSPlugin.objects.filter(page=page):
        if excludes:
            if plugin.pk in excludes:
                continue
        instance, admin = plugin.get_plugin_instance()
        if instance:
            instance.save()
        else:
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
    

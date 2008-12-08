from os.path import join
from inspect import isclass, getmembers

from django.forms import Widget, TextInput, Textarea, CharField
from django.contrib import admin
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils.encoding import force_unicode

from django.db import models
from django.http import HttpResponseRedirect
from django.contrib.admin.util import unquote

from cms import settings
from cms.models import Page, Content, tagging, Title
from cms.views import details
from cms.utils import get_template_from_request, has_page_add_permission, \
    get_language_from_request

import widgets
from cms.admin.forms import PageForm
from cms.admin.utils import get_placeholders
from cms.admin.views import traduction, get_content, valid_targets_list, \
    change_status, modify_content


class PageAdmin(admin.ModelAdmin):
    form = PageForm
    exclude = ['author', 'parent']
    # these mandatory fields are not versioned
    mandatory_placeholders = ('title', 'slug')
    general_fields = ['title', 'slug', 'status', 'sites', 'in_navigation', 'soft_root']
    insert_point = general_fields.index('status') + 1
    
    
    if settings.CMS_TAGGING:
        general_fields.insert(insert_point, 'tags')
    
    # Add support for future dating and expiration based on settings.
    if settings.CMS_SHOW_END_DATE:
        general_fields.insert(insert_point, 'publication_end_date')
    if settings.CMS_SHOW_START_DATE:
        general_fields.insert(insert_point, 'publication_date')

    normal_fields = ['language']
    if settings.CMS_TEMPLATES:
        normal_fields.append('template')

    fieldsets = (
        (_('General'), {
            'fields': general_fields,
            'classes': ('sidebar',),
        }),
        (_('Options'), {
            'fields': normal_fields,
            'classes': ('sidebar', 'clear'),
            'description': _('Note: This page reloads if you change the selection'),
        }),
    )
    
    list_filter = ('soft_root', 'status', 'in_navigation')
    search_fields = ('status',)
    
      
    class Media:
        css = {
            'all': [join(settings.CMS_MEDIA_URL, path) for path in (
                'css/rte.css',
                'css/pages.css'
            )]
        }
        js = [join(settings.CMS_MEDIA_URL, path) for path in (
            'javascript/jquery.js',
            'javascript/jquery.rte.js',
            'javascript/jquery.query.js',
            'javascript/change_form.js',
        )]

    def __call__(self, request, url):
        # Delegate to the appropriate method, based on the URL.
        if url is None:
            return self.list_pages(request)
        elif 'traduction' in url:
            page_id, action, language_id = url.split('/')
            return traduction(request, unquote(page_id), unquote(language_id))
        elif 'get-content' in url:
            page_id, action, content_id = url.split('/')
            return get_content(request, unquote(page_id), unquote(content_id))
        elif 'modify-content' in url:
            page_id, action, content_id, language_id = url.split('/')
            return modify_content(request, unquote(page_id),
                                    unquote(content_id), unquote(language_id))
        elif url.endswith('/valid-targets-list'):
            return valid_targets_list(request, unquote(url[:-19]))
        elif url.endswith('/move-page'):
            return self.move_page(request, unquote(url[:-10]))
        elif url.endswith('/change-status'):
            return change_status(request, unquote(url[:-14]))
        return super(PageAdmin, self).__call__(request, url)

    def save_model(self, request, obj, form, change):
        print "save model"
        """
        Move the page in the tree if neccesary and save every placeholder
        Content object.
        """
        obj.save()
        language = form.cleaned_data['language']
        target = request.GET.get('target', None)
        position = request.GET.get('position', None)
        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                pass
            else:
                obj.move_to(target, position)
        Title.objects.set_or_create(obj, language, form.cleaned_data['slug'], form.cleaned_data['title'])
        for placeholder in get_placeholders(request, obj.get_template()):
            if placeholder.name in form.cleaned_data:
                if placeholder.name not in self.mandatory_placeholders:
                    if change:                        
                            # we need create a new content if revision is enabled
                            #TODO: implement django-revision
                            if False and settings.CMS_CONTENT_REVISION and placeholder.name \
                                    not in settings.CMS_CONTENT_REVISION_EXCLUDE_LIST:
                                Content.objects.create_content_if_changed(obj, language,
                                    placeholder.name, form.cleaned_data[placeholder.name])
                            else:
                                Content.objects.set_or_create_content(obj, language,
                                    placeholder.name, form.cleaned_data[placeholder.name])
                    else:
                        Content.objects.set_or_create_content(obj, language,
                            placeholder.name, form.cleaned_data[placeholder.name])

    def get_fieldsets(self, request, obj=None):
        """
        Add fieldsets of placeholders to the list of already existing
        fieldsets.
        """
        placeholder_fieldsets = []
        template = get_template_from_request(request, obj)
        for placeholder in get_placeholders(request, template):
            print placeholder
            if placeholder.name not in self.mandatory_placeholders:
                placeholder_fieldsets.append(placeholder.name)

        if self.declared_fieldsets:
            given_fieldsets = list(self.declared_fieldsets)
        else:
            form = self.get_form(request, obj)
            given_fieldsets = [(_('content'), {'fields': form.base_fields.keys()})]
        return given_fieldsets + [(_('content'), {'fields': placeholder_fieldsets})]

    def save_form(self, request, form, change):
        """
        Given a ModelForm return an unsaved instance. ``change`` is True if
        the object is being changed, and False if it's being added.
        """
        instance = super(PageAdmin, self).save_form(request, form, change)
        instance.template = form.cleaned_data['template']
        if not change:
            instance.author = request.user
        return instance

    def get_widget(self, request, name):
        """
        Given the request and name of a placeholder return a Widget subclass
        like Textarea or TextInput.
        """
        widget = dict(getmembers(widgets, isclass)).get(name, Textarea)
        if not isinstance(widget(), Widget):
            widget = Textarea
        return widget

    def get_form(self, request, obj=None, **kwargs):
        """
        Get PageForm for the Page model and modify its fields depending on
        the request.
        """
        form = super(PageAdmin, self).get_form(request, obj, **kwargs)
        language = get_language_from_request(request, obj)
        form.base_fields['language'].initial = force_unicode(language)
        if obj:
            initial_slug = obj.get_slug(language=language, fallback=False)
            initial_title = obj.get_title(language=language, fallback=False)
            form.base_fields['slug'].initial = initial_slug
            form.base_fields['title'].initial = initial_title
        template = get_template_from_request(request, obj)
        if settings.CMS_TEMPLATES:
            template_choices = list(settings.CMS_TEMPLATES)
            template_choices.insert(0, (settings.DEFAULT_CMS_TEMPLATE, _('Default template')))
            form.base_fields['template'].choices = template_choices
            form.base_fields['template'].initial = force_unicode(template)
        for placeholder in get_placeholders(request, template):
            widget = self.get_widget(request, placeholder.widget)()
            if placeholder.name not in self.mandatory_placeholders:
                if obj:
                    initial = Content.objects.get_content(obj, language, placeholder.name)
                else:
                    initial = None
                form.base_fields[placeholder.name] = CharField(widget=widget, required=False, initial=initial)
        return form

    def change_view(self, request, object_id, extra_context=None):
        """
        The 'change' admin view for the Page model.
        """
        try:
            obj = self.model.objects.get(pk=object_id)
        except self.model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None
        else:
            template = get_template_from_request(request, obj)
            extra_context = {
                'placeholders': get_placeholders(request, template),
                'language': get_language_from_request(request),
                'traduction_language': settings.CMS_LANGUAGES,
                'page': obj,
            }
        return super(PageAdmin, self).change_view(request, object_id, extra_context)

    def has_add_permission(self, request):
        """
        Return true if the current user has permission to add a new page.
        """
        if not settings.CMS_PERMISSION:
            return super(PageAdmin, self).has_add_permission(request)
        else:
            return has_page_add_permission(request)

    def has_change_permission(self, request, obj=None):
        """
        Return true if the current user has permission on the page.
        Return the string 'All' if the user has all rights.
        """
        if settings.CMS_PERMISSION and obj is not None:
            return obj.has_page_permission(request)
        return super(PageAdmin, self).has_change_permission(request, obj)

    def list_pages(self, request, template_name=None, extra_context=None):
        """
        List root pages
        """
        # HACK: overrides the changelist template and later resets it to None
        if template_name:
            self.change_list_template = template_name
        context = {
            'name': _("page"),
            'pages': Page.objects.root().order_by("tree_id"),
        }
        context.update(extra_context or {})
        change_list = self.changelist_view(request, context)
        self.change_list_template = None
        return change_list

    def move_page(self, request, page_id, extra_context=None):
        """
        Move the page to the requested target, at the given position
        """
        context = {}
        page = Page.objects.get(pk=page_id)

        target = request.POST.get('target', None)
        position = request.POST.get('position', None)
        if target is not None and position is not None:
            try:
                target = self.model.objects.get(pk=target)
            except self.model.DoesNotExist:
                context.update({'error': _('Page could not been moved.')})
            else:
                page.move_to(target, position)
                return self.list_pages(request,
                    template_name='admin/cms/page/change_list_table.html')
        context.update(extra_context or {})
        return HttpResponseRedirect('../../')
admin.site.register(Page, PageAdmin)

class ContentAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'type', 'language', 'page')
    list_filter = ('page',)
    search_fields = ('body',)

admin.site.register(Content, ContentAdmin)
admin.site.register(Title)

if settings.CMS_PERMISSION:
    from cms.models import PagePermission
    admin.site.register(PagePermission)

# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import re

from django.contrib.admin.templatetags.admin_static import static
from django.core.urlresolvers import reverse
from django.conf.urls import url, patterns
from django.db import models
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils import six
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from cms.admin.placeholderadmin import FrontendEditableAdminMixin
from cms.models import CMSModelBase
from cms.utils import get_cms_setting

def _get_generic_cls_name(model, cls_type):
    """
    Returns a generic class name for given model and wanted class type.
    Returned class name uses this format : Generic<AppName><ModelName><cls_type>
    e.g: for model `great_library.models.Book` and wanted `cls_type` `'App'`, retured class name
    will be : `GenericGreatLibraryBookApp`.
    """
    infos = {
        'app_name': re.sub('[\W_]+', '', model._meta.app_label.title()),
        'model_name': model.__name__,
        'cls_type': cls_type,
    }
    return 'Generic{app_name}{model_name}{cls_type}'.format(**infos)

def modeladmin_frontend_mixin_cls_factory(admin_list_display_link=None,
                                          frontend_edit_link_short_description=None,
                                          frontend_edit_link_admin_order_field=None,):

    class klass(FrontendEditableAdminMixin):

        class Media:
            css = {
                "all": ("cms/css/cms.custom_model.css",)
            }

        def frontend_edit_link_label(self, obj, func_or_attr=None):
            if func_or_attr is not None:
                if isinstance(func_or_attr, six.string_types):
                    if hasattr(obj, func_or_attr):
                        attr = getattr(obj, func_or_attr)
                    elif hasattr(self, func_or_attr):
                        attr = getattr(self, func_or_attr)
                    else:
                        raise ValueError(
                            'func_or_attr is a string, it needs to be'
                            ' an object attribute (eventualy a function)'
                        )

                    if callable(attr):
                        title = attr(obj)
                    else:
                        title = attr

                elif callable(func_or_attr):
                    title = func_or_attr(obj)
                else:
                    raise ValueError('func_or_attr needs to be either a string or a collable')

            else:
                title = six.text_type(obj)
            return title

        def frontend_edit_link(self, obj, request):
            """creates the change list frontend edit link"""
            output_vars = {'label': self.frontend_edit_link_label(obj, admin_list_display_link)}
            if hasattr(obj, 'get_absolute_url'):
                output = '<a class="custommodel_title" href="{show_url}" target="_parent" title="{show_title}">{label}</a>'
                output_vars.update({
                    'show_url': '%s?%s' % (obj.get_absolute_url(), 
                                           get_cms_setting('CMS_TOOLBAR_URL__EDIT_ON')),
                    'show_title': _("edit on frontend") % obj._meta.verbose_name,
                })
            else:
                output = '<span class="custommodel_title">{label}</span>'
            return format_html(output, **output_vars)
        frontend_edit_link.allow_tags = True
        frontend_edit_link.short_description = frontend_edit_link_short_description
        frontend_edit_link.admin_order_field = frontend_edit_link_admin_order_field

        def action_links(self, obj, request):
            """creates the action list links"""
            admin_urls_prefix = 'admin:%s_%s' % (obj._meta.app_label, obj._meta.model_name)
            output, output_vars = '', {}
            if obj.has_change_permission(request):
                output += ('<a class="edit" href="{edit_url}" title="{edit_title}">'
                           '<span>{edit_label}</span></a>')
                output_vars.update({
                    'edit_title': _('%(model)s settings') % {'model': obj._meta.verbose_name, },
                    'edit_label': _('edit'),
                    'edit_url': reverse('%s_change' % admin_urls_prefix, args=[obj.pk]),
                })
            if obj.has_delete_permission(request):
                output += ('<a class="deletelink" href="{delete_url}" title="{delete_title}">'
                          '<span>{delete_label}</span></a>')
                output_vars.update({
                    'delete_title': _('delete'),
                    'delete_label': _('delete'),
                    'delete_url': reverse('%s_delete' % admin_urls_prefix, args=[obj.pk]),
                })
            if output:
                output = '<span class="cms_actions">%s</span>' % output
            return format_html(output, **output_vars)
        action_links.allow_tags = True
        action_links.short_description = _('actions')

        def get_list_display(self, request):
            list_display = super(FrontendEditableAdminMixin, self).get_list_display(request)
            list_display = list(list_display)
            del list_display[0]
            list_display.insert(0, 'frontend_edit_link')
            if 'action_links' not in list_display:
                list_display.append('action_links')
            return list_display

        def get_list_display_links(self, request, list_display):
            return [None, ]

    return klass

def modeladmin_bool_field_link_factory(field_name, field_label):
    """
    Creates and returns  a "list_display function" to have a clickable yes/no icon to
    switch the field value for the current object.
    """
    def switch_link(obj):
        value = getattr(obj, field_name)
        if value:
            title = _('Enable')
            icon_url = static('admin/img/icon-yes.gif')
        else:
            title = _('Disable')
            icon_url = static('admin/img/icon-no.gif')
        infos = (obj._meta.app_label, obj._meta.model_name, field_name)
        url = reverse('admin:admin_%s_%s_switch_%s' % infos, args=[obj.pk,])
        infos = (url, title, icon_url, value)
        #TODO: javascript for json call
        return u'<a href="%s" title="%s"><img src="%s" alt="%s" /></a>' % infos
    switch_link.short_description = field_label
    switch_link.allow_tags = True
    switch_link.admin_order_field = field_name
    switch_link.__name__ = str('%s_switcher' % field_name)
    switch_link.__doc__ = 'gets a clickable icon to switch "%s"' % field_name
    return switch_link

def modeladmin_get_urls_factory(modeladmin_cls, boolean_field_names=[]):
    """
    Creates and returns a ModelAdmin method to return a generic urls list related to generic
    methods (as "switch" views for boolean fields for exemple).
    For `boolean_field_names` list: 
        current ModelAdmin must have `switch_<field_name>` methods for each given field_name.
        Related url name will be `admin_<app_label>_<model_name>_switch_<field_name>`. 
        Related url path will be `^([0-9]+)/switch-<field_name>/`
        You can use `modeladmin_switch_bool_field_func_factory` to auto-build those methods.

    e.g: with `boolean_field_names = ('published', 'highlighted')` and modelAdmin of 
    `great_library.models.Book` as the current model admin, those urls will be generated :
        * `admin_great_library_book_switch_published` related to `self.switch_published` via
          url complete path `/admin/great_library/book/15/switch-published/` for pk 15
        * `admin_great_library_book_switch_highlighted` related to `self.switch_highlighted` via 
          url complete path `/admin/great_library/book/15/switch-highlighted/` for pk 15
    """

    def get_urls(self):
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        urls = super(modeladmin_cls, self).get_urls()
        my_urls = []
        for field_name in boolean_field_names:
            infos = (app_label, model_name, field_name)
            func = getattr(self, 'switch_%s' % field_name)
            my_urls.append(url(
                r'^([0-9]+)/switch-%s/$' % field_name,
                self.admin_site.admin_view(func),
                name='admin_%s_%s_switch_%s' % infos
            ))
        return patterns('', *my_urls) + urls
    get_urls.__doc__ = "Gets ModelAdmin's URLs with \"switch urls\" for boolean field"
    return get_urls

def modeladmin_switch_bool_field_func_factory(field_name):
    """
    Creates and returns a ModelAdmin view method to switch the value of a boolean field.
    Returned method view raises a 404 if object is not found, else it swiches the value of the related 
    field, then redirect to the list (related url path MUST looks like `^([0-9]+)/whatever/$`) or,
    if ajax, returns a dict with keys `obj_title` and `new_value`.
    e.g: with `field_name` = 'published', returned method will be equivalent to:

        def switch_published(self, request, obj_id):
            \"\"\"switches the "published" boolean field from True to False or vice versa\"\"\"
            obj = get_object_or_404(self.model, pk=obj_id)
            new_value = not obj.published
            obj.published = new_value
            obj.save()
            if request.is_ajax():
                return json.dumps({'obj_title': '%s' % obj, 'new_value': new_value,})
            else:
                return HttpResponseRedirect('../../')
        
    """
    def func(self, request, obj_id):
        obj = get_object_or_404(self.model, pk=obj_id)
        new_value = not getattr(obj, field_name)
        setattr(obj, field_name, new_value)
        obj.save()
        if request.is_ajax():
            return json.dumps({'obj_title': '%s' % obj, 'new_value': new_value,})
        else:
            return HttpResponseRedirect('../../')
    func.__name__ = str('switch_%s' % field_name)
    func.__doc__ = 'switches the "%s" boolean field from True to False or vice versa' % field_name
    return func

def modeladmin_cls_factory(model, auto_register=False):
    """
    Builds the "best" default AdminModel to manage the given CMSModel and auto register it 
    if wanted.
    
    Returned class will be named `Generic{AppLabel}{ModelName}Admin`. e.g for a model `Book` from 
    `great_library.models.py`, the generated app name will be `GenericGreatLibraryBookAdmin`.
    """

    if not issubclass(model, CMSModelBase):
        raise Exception('given model "%s" is not an instance of `CMSModelBase`' % model)

    from django.contrib import admin
    from cms.admin.generic import AddRequestToListdisplayAdminMixin, GenericAdmin
    from cms.models.fields import PlaceholderField

    cls_name = _get_generic_cls_name(model, 'Admin')
    cls_attrs = {
        'list_display':[],
        'search_fields':[],
        'list_filter':[],
        'fields':[],
        'ordering': model._meta.ordering,
    }

    title_field = None
    boolean_field_names = []

    for field in model._meta.fields:
        if isinstance(field, models.AutoField):
            continue

        add_list_display = False
        add_search_fields = False
        add_list_filter = False
        add_fields = True

        if issubclass(field.__class__, models.IntegerField):
            add_list_display = True
        elif issubclass(field.__class__, models.TextField):
            add_search_fields = True
        elif issubclass(field.__class__, models.CharField):
            if field.max_length <= 255:
                if not isinstance(field, models.SlugField) and (
                    title_field is None or field.name in ('title', 'name')):
                    title_field = field
                add_list_display = True
            add_search_fields = True
        elif issubclass(field.__class__, models.BooleanField):
            boolean_field_names.append(field.name)
            cls_attrs['switch_%s' % field.name] = modeladmin_switch_bool_field_func_factory(
                                                        field.name)
            cls_attrs['list_display'].append(
                modeladmin_bool_field_link_factory(field.name, field.verbose_name))
            add_list_display = False
            add_list_filter = True
        elif issubclass(field.__class__, PlaceholderField):
            add_fields = False
        elif isinstance(field, models.DateField):
            if not 'date_hierarchy' in cls_attrs:
                cls_attrs['date_hierarchy'] = field.name
        elif isinstance(field, models.ForeignKey):
            add_list_display = True

        if hasattr(field, 'choices'):
            add_search_fields = False
            add_list_filter = True

        if add_list_display:
            cls_attrs['list_display'].append(field.name)
        if add_search_fields:
            cls_attrs['search_fields'].append(field.name)
        if add_list_filter:
            cls_attrs['list_filter'].append(field.name)
        if add_fields:
            cls_attrs['fields'].append(field.name)

    if title_field is not None and model._cms_meta['slug_field_name'] != 'pk':
        cls_attrs['prepopulated_fields'] = {
            model._cms_meta['slug_field_name']: (title_field.name,)}

    if title_field:
        frontend_mixin_kwargs = {
            'admin_list_display_link': title_field.name,
            'frontend_edit_link_admin_order_field': title_field.name,
            'frontend_edit_link_short_description': title_field.verbose_name,
        }
    cls_bases = (
        AddRequestToListdisplayAdminMixin, 
        modeladmin_frontend_mixin_cls_factory(**frontend_mixin_kwargs), 
        GenericAdmin,)
    modeladmin_cls = type(str(cls_name), cls_bases, cls_attrs)

    generic_url_kwargs = {}
    if boolean_field_names:
        generic_url_kwargs['boolean_field_names'] = boolean_field_names
    if generic_url_kwargs:
        modeladmin_cls.get_urls = modeladmin_get_urls_factory(modeladmin_cls, **generic_url_kwargs)

    if auto_register:
        admin.site.register(model, modeladmin_cls)
    #TODO : checks that modelAdmin is coherent with the documented one.
    return modeladmin_cls

def cmsplugin_cls_factory(model, auto_register=False):
    """
    Builds the "best" default CMSPlugin subclass for the given CMSModel to display a list of 
    its instances and auto register it if wanted.
    
    Returned class will be named `Generic{AppLabel}{ModelName}ListPlugin`. e.g for a model `Book` 
    from `library.models.py`, the generated app name will be `GenericLibraryBookListPlugin`.
    """
    # TODO

def cmsattachmenu_cls_factory(model, auto_register=False):
    """
    Builds the "best" default ``CMSAttachMenu`` subclass for the given CMSModel to have a 
    submenu with all instances detail link and auto register it via ``menu_pool.register_menu`` 
    if wanted.

    Returned class will be named ``Generic{AppLabel}{ModelName}Menu``. e.g for a model ``Book`` 
    from ``library.models.py``, the generated app name will be ``GenericLibraryBookMenu``.
    """
    #TODO

def cmsapp_cls_factory(model, app_name=None, auto_register=False):
    """
    Builds the "best" default ModelApp for the current model and auto register it if wanted.
    
    Returned class will be named `Generic{AppLabel}{ModelName}App`. e.g for a model `Book` from 
    `library.models.py`, the generated app name will be `GenericLibraryBookApp`.
    """
    
    if not issubclass(model, CMSModelBase):
        raise Exception('given model "%s" is not an instance of `CMSModelBase`' % model)
    
    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from cms.views import CustomModelDetailView, CustomModelListView

    cls_name = _get_generic_cls_name(model, 'App')
    cls_bases = (CMSApp,)
    cls_attrs = {
        'name': model._meta.verbose_name_plural,
    }

    #set app urls config
    urls = []
    if model._cms_meta['list_view']:
        urls.append(url(r'^$', CustomModelListView.as_view(model=model), 
                        name=model._cms_meta['list_view_url_name']))
    if model._cms_meta['detail_view']:
        if model._cms_meta['slug_field_name'] != 'pk':
            regex = r'^(?P<{0}>[\w-]+)/$'.format(model._cms_meta['slug_field_name'])
        else:
            regex = r'^(?P<pk>[0-9]+)/$'
        urls.append(url(regex, CustomModelDetailView.as_view(model=model), 
                        name=model._cms_meta['detail_view_url_name']))
    cls_attrs['urls'] = patterns('', *urls)

    apphook_cls = type(str(cls_name), cls_bases, cls_attrs)
    if auto_register:
        apphook_pool.register(apphook_cls)
    #TODO : checks that apphook_cls is coherent with the documented one.
    return apphook_cls

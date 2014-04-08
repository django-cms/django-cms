# -*- coding: utf-8 -*-
import re

from django.db import models
from django.utils.translation import ugettext as _
from django.contrib.admin.templatetags.admin_static import static
from django.core.urlresolvers import reverse
from django.conf.urls import url, patterns
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from cms.app_base import GenericCMSModelAppMetaClass

def _get_generic_cls_name(model, 'App'):
    cls_name = 'Generic{app}{model}{cls_type}'
    return cls_name.format(app=re.sub('[\W_]+', '', model._meta.app_label.title()), 
                           model=model.__name__, 
                           cls_type=cls_type)

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
        url = reverse('admin:admin_%s_%s_change_%s' % infos, args=[obj.pk,])
        infos = (url, title, icon_url, value)
        return u'<a href="%s" title="%s"><img src="%s" alt="%s" /></a>' % infos
    switch_link.short_description = field_label
    switch_link.allow_tags = True
    switch_link.admin_order_field = field_name
    switch_link.__name__ = '%s_switcher' % field_name
    switch_link.__doc__ = 'gets a clickable icon to switch "%s"' % field_name
    return switch_link

def modeladmin_get_urls_factory(model, boolean_field_names=[],):
    """
    Creates and returns  a function to return urls with all boolean "change" views.
    """
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    def get_urls(self):
        urls = super(type(self), self).get_urls()
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

def modeladmin_change_bool_field_func_factory(field_name):
    """
    Creates and returns a view function to switch the value of a boolean field
    """
    def func(self, request, obj_id):
        obj = get_object_or_404(self.model, pk=obj_id)
        new_value = not getattr(obj, field_name)
        setattr(obj, field_name, new_value)
        obj.save()
        #TODO : Ajax 
        return HttpResponseRedirect('../../')
    func.__name__ = 'switch_%s' % field_name
    func.__doc__ = 'switches the "%s" boolean field from True to False or vice versa' % field_name
    return func

def modeladmin_cls_factory(model, auto_register=False):
    """
    Builds the "best" default AdminModel to manage the given CMSModel and auto register it 
    if wanted.
    
    Returned class will be named `Generic{AppLabel}{ModelName}Admin`. e.g for a model `Book` from 
    `library.models.py`, the generated app name will be `GenericLibraryBookAdmin`.
    """
    
    # TODO check that the ModelAdmin subclass is coherent with the documented one in cms_model.rst
    
    from django.contrib import admin
    from cms.admin.generic import GenericAdmin
    from cms.models.fields import PlaceholderField

    cls_name = _get_generic_cls_name(model, 'Admin')
    cls_bases = (GenericAdmin,)
    cls_attrs = {
        'list_display':[],
        'search_fields':[],
        'list_filter':[],
        'fields':[],
        'ordering': model._meta.ordering,
    }

    title_field = ''
    boolean_field_names = []

    for field in model._meta.fields:
        if isinstance(field, models.AutoField):
            continue

        add_list_display = False
        add_search_fields = False
        add_list_filter = False
        add_fields = True

        if isinstance(field, models.CharField):
            if field.max_length <= 255:
                if not isinstance(field, models.SlugField) and (
                    title_field == '' or field.name in ('title', 'name')):
                    title_field = field.name
                add_list_display = True
            if field.choices:
                add_search_fields = False
                add_list_filter = True
            else:
                add_search_fields = True
        elif isinstance(field, models.IntegerField):
            add_list_display = True
        elif isinstance(field, models.TextField):
            add_search_fields = True
        elif isinstance(field, models.BooleanField):
            boolean_field_names.append(field.name)
            cls_attrs['list_display'].append(
                modeladmin_bool_field_link_factory(field.name, field.verbose_name))
            add_list_display = False
            add_list_filter = True
            
        elif isinstance(field, models.DateField):
            if not 'date_hierarchy' in cls_attrs:
                cls_attrs['date_hierarchy'] = field.name
        elif isinstance(field, PlaceholderField):
            add_fields = False
        elif isinstance(field, models.ForeignKey):
            add_list_display = True

        if add_list_display:
            cls_attrs['list_display'].append(field.name)
        if add_search_fields:
            cls_attrs['search_fields'].append(field.name)
        if add_list_filter:
            cls_attrs['list_filter'].append(field.name)
        if add_fields:
            cls_attrs['fields'].append(field.name)

    if title_field != '' and model._cms_meta['slug_field_name'] != 'pk':
        cls_attrs['prepopulated_fields'] = {
            model._cms_meta['slug_field_name']: (title_field,)}

    if boolean_field_names:
        cls_attrs['get_urls'] = modeladmin_get_urls_factory(
            model=model, 
            boolean_field_names=boolean_field_names)
        for field_name in boolean_field_names:
            func_name = 'change_%s' % field_name
            cls_attrs[func_name] = modeladmin_change_bool_field_func_factory(field_name)

    modelAdmin = type(cls_name, cls_bases, cls_attrs)
    if auto_register:
        admin.site.register(model, modelAdmin)
    return modelAdmin

def cmsplugin_cls_factory(model, auto_register=False):
    """
    Builds the "best" default CMSPlugin subclass for the given CMSModel to display a list of 
    its instances and auto register it if wanted.
    
    Returned class will be named `Generic{AppLabel}{ModelName}ListPlugin`. e.g for a model `Book` 
    from `library.models.py`, the generated app name will be `GenericLibraryBookListPlugin`.
    """
    # TODO build a CMSPLugin subclass that is coherent with the documented one in cms_model.rst

def cmsapp_cls_factory(model, app_name=None, auto_register=False):
    """
    Builds the "best" default ModelApp for the current model and auto register it if wanted.
    
    Returned class will be named `Generic{AppLabel}{ModelName}App`. e.g for a model `Book` from 
    `library.models.py`, the generated app name will be `GenericLibraryBookApp`.
    """
    
    # TODO check that the AppHoob subclass is coherent with the documented one in cms_model.rst
    
    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool

    cls_name = _get_generic_cls_name(model, 'App')
    cls_bases = (CMSApp,)
    cls_attrs = {
        'name': model._meta.verbose_name_plural,
        'urls': patterns('', *urls)
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

    Apphook = type(cls_name, cls_bases, cls_attrs)
    if auto_register:
        apphook_pool.register(Apphook)
    return Apphook

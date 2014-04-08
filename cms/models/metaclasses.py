# -*- coding: utf-8 -*-
from cms.publisher.manager import PublisherManager
from mptt.models import MPTTModelBase
from django.db.models import SlugField
from django.db.models.base import ModelBase
from cms.models._registry import CMSModelsRegistry

def _default_get_absolute_url(self, *args, **kwargs):
    """
    Get the absolute URL for the current instance. 
    Default behaviour is to build an url with "url_name_detail" and the 
    slug field of the instance if exists, else with the pk.
    """
    return reverse(self._cms_meta['detail_view_url_name'], 
                   args=(self.get_slug(),))

class CMSModelMetaClass(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(CMSModelMetaClass, cls).__new__

        # attrs will never be empty for classes declared in the standard way
        # (ie. with the `class` keyword). This is quite robust.
        if name == 'NewBase' and attrs == {}:
            return super_new(cls, name, bases, attrs)

        # Also ensure initialization is only performed for subclasses of 
        # CMSModelMetaClass (excluding CMSModelMetaClass class itself).
        parents = [b for b in bases if isinstance(b, CMSModelMetaClass) and
                not (b.__name__ == 'NewBase' and b.__mro__ == (b, object))]
        if not parents:
            return super_new(cls, name, bases, attrs)

        attr_meta = attrs.get('Meta', None)
        abstract = getattr(attr_meta, 'abstract', False)
        cms_opts = {}
        
        cms_opts_default_values = {
            'create_admin_model': True,
            'create_plugin': True,
            'create_app': True,
            'add_to_cms_toolbar': False,
            'detail_view': True,
            'list_view': True,
            'detail_view_url_name': None,
            'list_view_url_name': None,
            'slug_field_name': None,
        }

        for opt in cms_opts_default_values:
            cms_opt = 'cms_' + opt
            if hasattr(attr_meta, cms_opt):
                cms_opts[opt] = getattr(attr_meta, cms_opt)
                delattr(attr_meta, cms_opt)

        if not abstract:
            for opt in cms_opts_default_values:
                if not opt in cms_opts:
                    cms_opts[opt] = cms_opts_default_values[opt]
            app_label = getattr(attr_meta, 'app_label', attrs['__module__'])
            app_label = app_label.split('.')[0].lower()

            if cms_opts['detail_view']:
                set_default_get_absolute_url = 'get_absolute_url' not in attrs
                if set_default_get_absolute_url:
                    for base in bases:
                        if hasattr(base, 'get_absolute_url'):
                            set_default_get_absolute_url = False
                            break
                    if set_default_get_absolute_url:
                        attrs['get_absolute_url'] = _default_get_absolute_url

                if not cms_opts['detail_view_url_name']:
                    """
                    Adds the detail_view_url_name to _cms_meta. if not defined, we build the
                    default one with this format : <app_label>_<model_name>_detail
                    Names are lowered.
                    """
                    cms_opts['detail_view_url_name'] = "%s_%s_detail" % (app_label, name.lower())

            if cms_opts['list_view'] and not cms_opts['list_view_url_name']:
                """
                Adds the list_view_url_name to _cms_meta. if not defined, we build the
                default one with this format : <app_label>_<model_name>_list
                Names are lowered.
                """
                cms_opts['list_view_url_name'] = "%s_%s_list" % (app_label, name.lower())

            #Find the SlugField to use for this model. If there is no SlugField,
            #pk is used instead.
            if not cms_opts['slug_field_name']:
                if 'slug' in attrs and isinstance(attrs['slug'], SlugField):
                    cms_opts['slug_field_name'] = 'slug'
                else:
                    for field_name in attrs:
                        if isinstance(attrs[field_name], SlugField):
                            cms_opts['slug_field_name'] = field_name
                            break
                    if not cms_opts['slug_field_name']:
                        cms_opts['slug_field_name'] = 'pk'

        attrs['_cms_meta'] = cms_opts
        model = super_new(cls, name, bases, attrs)
        if not abstract:
            CMSModelsRegistry.add_item(model)
                
        return model


class PageMetaClass(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(PageMetaClass, cls).__new__

        if 'objects' in attrs:
            if not isinstance(attrs['objects'], PublisherManager):
                raise ValueError("Model %s extends Publisher, "
                                 "so its 'objects' manager must be "
                                 "a subclass of publisher.PublisherManager") % (name,)
        else:
            attrs['objects'] = PublisherManager()
        return super_new(cls, name, bases, attrs)

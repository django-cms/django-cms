# -*- coding: utf-8 -*-

class CMSModelsRegistry:
    items = {}

    @staticmethod
    def _auto_build():
        for configs in CMSModelsRegistry.items.values():
            for item in configs:
                model = item['model']
                if model._cms_meta['create_admin_model']:
                    from cms.utils.generic import modeladmin_cls_factory
                    modeladmin_cls_factory(model, auto_register=True)
                if model._cms_meta['create_plugin']:
                    from cms.utils.generic import cmsplugin_cls_factory
                    cmsplugin_cls_factory(model, auto_register=True)
                if model._cms_meta['create_app']:
                    from cms.utils.generic import cmsapp_cls_factory
                    cmsapp_cls_factory(model, auto_register=True)

    @staticmethod
    def add_item(model):
        """Adds a custom model to the list of CMS Model's"""

        from cms.models import CMSModelBase
        if not issubclass(model, CMSModelBase):
            raise ValueError("Model %s is not subclassing CMSModelBase." % (model.__name__,))

        app_label = model._meta.app_label
        if not app_label in CMSModelsRegistry.items:
            CMSModelsRegistry.items[app_label] = []
        item = {
            'model': model,
            'add_to_cms_toolbar' : model._cms_meta['add_to_cms_toolbar'],
            'title': model._meta.verbose_name_plural.title(),
        }
        CMSModelsRegistry.items[app_label].append(item)

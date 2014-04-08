# -*- coding: utf-8 -*-
class CMSApp(object):
    name = None
    urls = None
    menus = []
    app_name = None
    app_config = None
    permissions = True
    exclude_permissions = []

    def __new__(cls):
        """
        We want to bind the CMSapp class to a specific AppHookConfig, but only one at a time
        Checking for the runtime attribute should be a sane fix
        """
        if cls.app_config:
            if getattr(cls.app_config, 'cmsapp', None) and cls.app_config.cmsapp != cls:
                raise RuntimeError(
                    'Only one AppHook per AppHookConfiguration must exists.\n'
                    'AppHook %s already defined for %s AppHookConfig' % (
                        cls.app_config.cmsapp.__name__, cls.app_config.__name__
                    )
                )
            cls.app_config.cmsapp = cls
        return super(CMSApp, cls).__new__(cls)

    def get_configs(self):
        raise NotImplemented('Configurable AppHooks must implement this method')

    def get_config(self, namespace):
        raise NotImplemented('Configurable AppHooks must implement this method')

    def get_config_add_url(self):
        raise NotImplemented('Configurable AppHooks must implement this method')


class GenericCMSModelAppMetaClass(CMSApp):
    def __new__(cls, name, bases, attrs):
        import pdb
        pdb.set_trace()
        super_new = super(GenericCMSModelAppMetaClass, cls).__new__

        # attrs will never be empty for classes declared in the standard way
        # (ie. with the `class` keyword). This is quite robust.
        if name == 'NewBase' and attrs == {}:
            return super_new(cls, name, bases, attrs)

        # Also ensure initialization is only performed for subclasses of 
        # CMSModelMetaClass (excluding CMSModelMetaClass class itself).
        parents = [b for b in bases if isinstance(b, GenericCMSModelAppMetaClass) and
                   not (b.__name__ == 'NewBase' and b.__mro__ == (b, object))]
        if not parents:
            return super_new(cls, name, bases, attrs)
        
        if 'model' in attrs:
            import pdb
            pdb.set_trace()
            pass

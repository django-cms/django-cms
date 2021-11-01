from abc import ABCMeta, abstractmethod


class CMSApp:
    #: list of urlconfs: example: ``_urls = ["myapp.urls"]``
    _urls = []
    #: list of menu classes: example: ``_menus = [MyAppMenu]``
    _menus = []
    #: name of the apphook (required)
    name = None
    #: name of the app, this enables Django namespaces support (optional)
    app_name = None
    #: configuration model (optional)
    app_config = None
    #: if set to true, apphook inherits permissions from the current page
    permissions = True
    #: list of application names to exclude from inheriting CMS permissions
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
        return super().__new__(cls)

    def get_configs(self):
        """
        Returns all the apphook configuration instances.
        """
        raise NotImplementedError('Configurable AppHooks must implement this method')

    def get_config(self, namespace):
        """
        Returns the apphook configuration instance linked to the given namespace
        """
        raise NotImplementedError('Configurable AppHooks must implement this method')

    def get_config_add_url(self):
        """
        Returns the url to add a new apphook configuration instance
        (usually the model admin add view)
        """
        raise NotImplementedError('Configurable AppHooks must implement this method')

    def get_menus(self, page=None, language=None, **kwargs):
        """
        Returns the menus for the apphook instance, eventually selected according
        to the given arguments.

        By default it returns the menus assigned to :py:attr:`CMSApp._menus`.

        If no menus are returned, then the user will need to attach menus to pages
        manually in the admin.

        This method must return all the menus used by this apphook if no arguments are
        provided. Example::

            if page and page.reverse_id == 'page1':
                return [Menu1]
            elif page and page.reverse_id == 'page2':
                return [Menu2]
            else:
                return [Menu1, Menu2]

        :param page: page the apphook is attached to
        :param language: current site language
        :return: list of menu classes
        """
        return self._menus

    def get_urls(self, page=None, language=None, **kwargs):
        """
        Returns the urlconfs for the apphook instance, eventually selected
        according to the given arguments.

        By default it returns the urls assigned to :py:attr:`CMSApp._urls`

        This method **must** return a non empty list of urlconfs,
        even if no argument is passed.

        :param page: page the apphook is attached to
        :param language: current site language
        :return: list of urlconfs strings
        """
        return self._urls


class CMSAppConfig():
    """Base class that all cms app configurations should inherit from"""

    def __init__(self, django_app_config):
        self.app_config = django_app_config


class CMSAppExtension(metaclass=ABCMeta):
    """Base class that all cms app extensions should inherit from"""

    @abstractmethod
    def configure_app(self, cms_config):
        """
        Implement this method if the app provides functionality that
        other apps can use and configure.

        This method will be run once for every app that defines an
        attribute like "<app_label>_enabled" as True on its cms app
        config class.
        So for example if app A with label "app_a" implements this
        method and app B and app C define app_a_enabled = True on their
        cms config classes, the method app A has defined will run twice,
        once for app B and once for app C.

        :param cms_config: the cms config class of the app
        """
        pass

    def ready(self):
        """Override this method to run code after all CMS extensions
        have been configured.

        This method will be run once, even if no cms app config sets
        its "<app_label>_enabled" attribute to True"""
        pass

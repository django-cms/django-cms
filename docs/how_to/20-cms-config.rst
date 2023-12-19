How to share capabilities between apps
======================================

.. versionadded:: 4.0

To understand how to use the app registration system, lets use an example. Let's say our
``INSTALLED_APPS`` include these three apps:

.. code-block::

    INSTALLED_APPS = [
        ...
        'pink_cms_admin',
        'pony_cms_icons',
        'blog_posts',
    ]

The ``pink_cms_admin`` is an app that extends the cms by making apps, that are
accordingly configured, to have a pink admin. To do that, it would define a
``pink_cms_admin/cms_config.py`` file, which would look like this:

.. code-block::

    from cms.app_base import CMSAppExtension

    from pink_cms_admin import make_admin_pink


    class PinkAdminCMSExtension(CMSAppExtension):

        def configure_app(self, cms_config):
             # Do anything you need to do to each app that wants to be pink
             make_admin_pink(cms_config)

The ``blog_posts`` app wants to be pink and wants to have pony icons everywhere. So it
would define ``blog_posts/cms_config.py`` like this:

.. code-block::

    from cms.app_base import CMSAppConfig


    class BlogPostsCMSConfig(CMSAppConfig):
        # To enable functionality define an attribute like <app_label>_enabled
        # and set it to True
        pink_cms_admin_enabled = True
        pony_cms_icons_enabled = True

        # pony_cms_icons also has additional settings. These are defined here.
        pony_cms_icons_pony_colours = ['purple', 'pink']
        pony_cms_icons_ponies_with_wings = True

The pony_cms_icons app lets other apps have pony icons everywhere, but also wants to
have a pink admin. So it would define ``pony_cms_icons/cms_config.py`` like this:

.. code-block::

    from django.core.exceptions import ImproperlyConfigured

    from cms.app_base import CMSAppConfig, CMSAppExtension

    from pony_cms_icons import add_pony_icons


    class PonyIconsCMSConfig(CMSAppConfig):
        pink_cms_admin_enabled = True


    class PonyIconsCMSExtension(CMSAppExtension):

        def configure_app(self, cms_config):
             # Do anything you need to do to each app that wants to have
             # pony icons here

             # As pony icons defines additional settings, you will also need to check
             # for any required settings here
             pony_colours = getattr(cms_config, 'pony_cms_icons_pony_colours', None)
             if not pony_colours:
                 raise ImproperlyConfigured(
                     "Apps that use pony_cms_icons, must define pony_cms_icons_pony_colours")
             ponies_with_wings = getattr(cms_config, 'pony_cms_icons_ponies_with_wings', False)

             add_pony_icons(cms_config.django_app, pony_colours, ponies_with_wings)

The :meth:`~cms.app_base.CMSAppExtension.configure_app` method, as is already apparent,
takes one param - ``cms_config``. ``cms_config`` is an instance of an app's
:class:`~cms.app_base.CMSAppConfig` class. In addition to that you can also access the
django app object (as defined in the app's apps.py) by using ``cms_config.app_config``.
In this way you can access attributes that django provides (such as ``label``,
``verbose_name`` etc.).

The :meth:`~cms.app_base.CMSAppExtension.configure_app` method is run once for every
django cms app that declares a feature as enabled.

If an app asks for a feature of another app that is not installed this feature is simply
ignored. This in turn implies that you cannot assume that the feature you request in a
:class:`~cms.app_base.CMSAppConfig` is also available. Therefore, make sure your app's
code also runs without that feature or check if your providing app is present in your
:class:`~cms.app_base.CMSAppConfig` and raise an ``ImproperlyConfigured`` exception if
it is missing.

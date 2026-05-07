########################################
Configuring apps to work with django CMS
########################################

..  module:: cms.app_base

*********
App Hooks
*********

.. autoclass:: cms.app_base.CMSApp
    :members:

    .. attribute:: _urls

        list of urlconfs: example: ``_urls = ["myapp.urls"]``

    .. attribute:: _menus

        list of menu classes: example: ``_menus = [MyAppMenu]``

    .. attribute:: _root_template

        .. versionadded:: 5.1

        Template name used by the apphook's root view, consulted by the
        structure board when rendering placeholders on an apphooked page.
        If left as ``None`` (the default), :meth:`get_root_template` will
        try to infer it from the root URL pattern. Set this explicitly
        when inference is not possible — for example, when the root view
        is a function-based view, or selects its template at runtime.
        Example: ``_root_template = "myapp/home.html"``.


**********
App Config
**********

.. autoclass:: cms.app_base.CMSAppConfig
    :members:


**************
App Extensions
**************

.. autoclass:: cms.app_base.CMSAppExtension
    :members:



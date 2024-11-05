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



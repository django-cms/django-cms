########
Apphooks
########

..  module:: cms.app_base

..  class:: CMSApp

    ``CMSApp`` is the base class for django CMS apphooks.

    .. attribute:: _urls

        list of urlconfs: example: ``_urls = ["myapp.urls"]``

    .. attribute:: _menus

        list of menu classes: example: ``_menus = [MyAppMenu]``

    .. attribute:: name = None

        name of the apphook (required)

    .. attribute:: app_name = None

        name of the app, this enables Django namespaces support (optional)

    .. attribute:: app_config = None

        configuration model (optional)

    .. attribute:: permissions = True

        if set to true, apphook inherits permissions from the current page

    .. attribute:: exclude_permissions = []

        list of application names to exclude from inheriting CMS permissions


    .. method:: get_configs()

        Returns all the apphook configuration instances.

    .. method:: get_config(namespace)

        Returns the apphook configuration instance linked to the given namespace

    .. method:: get_config_add_url()

        Returns the url to add a new apphook configuration instance
        (usually the model admin add view)

    .. method:: get_menus(page, language, **kwargs)

            Returns the menus for the apphook instance, eventually selected according
            to the given arguments.

            By default it returns the menus assigned to :attr:`cms.app_base.CMSApp._menus`

            If no page and language si provided, this method **must** return all the
            menus used by this apphook. Example::

                if page and page.reverse_id == 'page1':
                    return [Menu1]
                elif page and page.reverse_id == 'page2':
                    return [Menu2]
                else:
                    return [Menu1, Menu2]

            :param page: page the apphook is attached to
            :param language: current site language
            :return: list of menu classes

    .. method:: get_urls(page, language, **kwargs)

            Returns the urlconfs for the apphook instance, eventually selected
            according to the given arguments.

            By default it returns the urls assigned to :py:attr:`cms.app_base.CMSApp._urls`

            This method **must** return a non empty list of urlconfs,
            even if no argument is passed.

            :param page: page the apphook is attached to
            :param language: current site language
            :return: list of urlconfs strings

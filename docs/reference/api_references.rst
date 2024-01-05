##############
API References
##############

*******
cms.api
*******

Python APIs for creating CMS content. This is done in :mod:`cms.api` and not
on the models and managers, because the direct API via models and managers is
slightly counterintuitive for developers. Also the functions defined in this
module do sanity checks on arguments.

.. warning:: None of the functions in this module does any security or permission
             checks. They verify their input values to be sane wherever
             possible, however permission checks should be implemented manually
             before calling any of these functions.

.. note:: Due to potential circular dependency issues, it's recommended
          to import the api in the functions that uses its function.

          e.g. use:

          ::

              def my_function():
                  from cms.api import api_function
                  api_function(...)

          instead of:

          ::

              from cms.api import api_function

              def my_function():
                  api_function(...)


Functions and constants
=======================

.. module:: cms.api

.. autofunction:: cms.api.create_page

.. autofunction:: cms.api.create_page_content

.. autofunction:: cms.api.create_title

.. autofunction:: cms.api.add_plugin

.. autofunction:: cms.api.create_page_user

.. autofunction:: cms.api.assign_user_to_page

.. autofunction:: cms.api.publish_page

.. autofunction:: cms.api.publish_pages

.. autofunction:: cms.api.get_page_draft

.. autofunction:: cms.api.copy_plugins_to_language

.. autofunction:: cms.api.can_change_page



Example workflows
=================

Create a page called ``'My Page`` using the template ``'my_template.html'`` and
add a text plugin with the content ``'hello world'``. This is done in English::

    from cms.api import create_page, add_plugin

    page = create_page('My Page', 'my_template.html', 'en')
    placeholder = page.placeholders.get(slot='body')
    add_plugin(placeholder, 'TextPlugin', 'en', body='hello world')


*************
cms.constants
*************

..  module:: cms.constants

.. autodata:: VISIBILITY_ALL

.. autodata:: VISIBILITY_USERS

.. autodata:: VISIBILITY_ANONYMOUS

.. autodata:: TEMPLATE_INHERITANCE_MAGIC

.. autodata:: LEFT
     :no-value:

.. autodata:: RIGHT
     :no-value:

.. autodata:: EXPIRE_NOW

.. autodata:: MAX_EXPIRATION_TTL


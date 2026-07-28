.. _plugins:

Plugins
=======

.. seealso::

    - :ref:`How django CMS is composed <composition>` — where plugins
      fit alongside pages and apphooks, including the plugin-vs-apphook
      decision aid.
    - :ref:`Plugins how-to guide <custom-plugins>`

CMS Plugins are reusable content publishers that can be inserted into django CMS pages
(or indeed into any content that uses django CMS placeholders). They enable the
publishing of information automatically, without further intervention.

This means that your published web content, whatever it is, is kept up-to-date at all
times.

It's like magic, but quicker.

Unless you're lucky enough to discover that your needs can be met by the built-in
plugins, or by the many available third-party plugins, you'll have to write your own
custom CMS Plugin.

*Why* would you need to write a plugin?
---------------------------------------

A plugin is the most convenient way to integrate content from another Django application
into a django CMS page.

For example, suppose you're developing a site for a record company in django CMS. You
might like to have a "Latest releases" box on your site's home page.

Of course, you could every so often edit that page and update the information. However,
a sensible record company will manage its catalogue in Django too, which means Django
already knows what this week's new releases are.

This is an excellent opportunity to make use of that information to make your life
easier - all you need to do is create a django CMS plugin that you can insert into your
home page, and leave it to do the work of publishing information about the latest
releases for you.

Plugins are **reusable**. Perhaps your record company is producing a series of reissues
of seminal Swiss punk records; on your site's page about the series, you could insert
the same plugin, configured a little differently, that will publish information about
recent new releases in that series.

Components of a plugin
----------------------

A django CMS plugin is fundamentally composed of three components, that correspond to
Django's familiar Model-View-Template scheme:

=================== ============================= ===================================
What                Function                      Subclass of
=================== ============================= ===================================
model (if required) plugin instance configuration :class:`CMSPlugin
                                                  <cms.models.pluginmodel.CMSPlugin>`
view                display logic                 :class:`CMSPluginBase
                                                  <cms.plugin_base.CMSPluginBase>`
template            rendering                     --
=================== ============================= ===================================

:class:`CMSPlugin <cms.models.pluginmodel.CMSPlugin>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin **model**, the sub-class of :class:`cms.models.pluginmodel.CMSPlugin`, is
optional.

You could have a plugin that doesn't need to be configured, because it only ever does
one thing.

For example, you could have a plugin that only publishes information about the
top-selling record of the past seven days. Obviously, this wouldn't be very flexible -
you wouldn't be able to use the same plugin for the best-selling release of the last
*month* instead.

Usually, you find that it is useful to be able to configure your plugin, and this will
require a model.

:class:`CMSPluginBase <cms.plugin_base.CMSPluginBase>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`cms.plugin_base.CMSPluginBase` is actually a sub-class of
:class:`django:django.contrib.admin.ModelAdmin`.

Because :class:`~cms.plugin_base.CMSPluginBase` sub-classes ``ModelAdmin`` several
important ``ModelAdmin`` options are also available to CMS plugin developers. These
options are often used:

- ``exclude``
- ``fields``
- ``fieldsets``
- ``form``
- ``formfield_overrides``
- ``inlines``
- ``radio_fields``
- ``raw_id_fields``
- ``readonly_fields``

Please note, however, that not all ``ModelAdmin`` options are effective in a CMS plugin.
In particular, any options that are used exclusively by the ``ModelAdmin``'s
``changelist`` will have no effect. These and other notable options that are ignored by
the CMS are:

- ``actions``
- ``actions_on_top``
- ``actions_on_bottom``
- ``actions_selection_counter``
- ``date_hierarchy``
- ``list_display``
- ``list_display_links``
- ``list_editable``
- ``list_filter``
- ``list_max_show_all``
- ``list_per_page``
- ``ordering``
- ``paginator``
- ``prepopulated_fields``
- ``preserve_fields``
- ``save_as``
- ``save_on_top``
- ``search_fields``
- ``show_full_result_count``
- ``view_on_site``

Beyond Python plugins: djangocms-frontend
-----------------------------------------------

Every plugin described so far requires a Python class — a
``CMSPluginBase`` subclass, and usually a model.
`djangocms-frontend <https://github.com/django-cms/djangocms-frontend>`_
offers two lighter-weight paths to a plugin, both translated into full
django CMS plugins under the hood:

**Template components.** Write a Django template, place it in a
``cms_components`` directory inside one of your apps, and
djangocms-frontend auto-detects it at startup. Fields are declared in
the template itself — no Python file is needed.

**Custom components.** Write a Python class (subclassing
``CMSFrontendComponent``) in a ``cms_components.py`` file, declare its
fields as Django form field attributes, and register it with the
``@components.register`` decorator. This gives you full control over
the add and change forms — fieldsets, custom validation, mixins —
while still avoiding the boilerplate of a full ``CMSPluginBase``
subclass.

Both paths are framework-agnostic (the built-in components and mixins
that ship with djangocms-frontend target Bootstrap 5, but you are not
tied to it). Their trade-off is scope: template components cannot
contain Python code at all, and custom components cannot add methods
to the plugin or model class. When you need that full control, a
``CMSPluginBase`` subclass is the right tool.

For step-by-step tutorials and examples, see the `djangocms-frontend
documentation <https://djangocms-frontend.readthedocs.io>`_.

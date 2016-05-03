#############
Template Tags
#############

*****************
CMS template tags
*****************

.. highlightlang:: html+django

To use any of the following template tags you first need to load them at the
top of your template::

    {% load cms_tags %}

.. template tag:: placeholder

placeholder
===========
.. versionchanged:: 2.1
    The placeholder name became case sensitive.

The ``placeholder`` template tag defines a placeholder on a page. All
placeholders in a template will be auto-detected and can be filled with
plugins when editing a page that is using said template. When rendering, the
content of these plugins will appear where the ``placeholder`` tag was.

Example::

    {% placeholder "content" %}

If you want additional content to be displayed in case the placeholder is
empty, use the ``or`` argument and an additional ``{% endplaceholder %}``
closing tag. Everything between ``{% placeholder "..." or %}`` and ``{%
endplaceholder %}`` is rendered in the event that the placeholder has no plugins or
the plugins do not generate any output.

Example::

    {% placeholder "content" or %}There is no content.{% endplaceholder %}

If you want to add extra variables to the context of the placeholder, you
should use Django's :ttag:`with` tag. For instance, if you want to re-size images
from your templates according to a context variable called ``width``, you can
pass it as follows::

    {% with 320 as width %}{% placeholder "content" %}{% endwith %}

If you want the placeholder to inherit the content of a placeholder with the
same name on parent pages, simply pass the ``inherit`` argument::

    {% placeholder "content" inherit %}

This will walk up the page tree up until the root page and will show the first
placeholder it can find with content.

It's also possible to combine this with the ``or`` argument to show an
ultimate fallback if the placeholder and none of the placeholders on parent
pages have plugins that generate content::

    {% placeholder "content" inherit or %}There is no spoon.{% endplaceholder %}

See also the :setting:`CMS_PLACEHOLDER_CONF` setting where you can also add extra
context variables and change some other placeholder behaviour.

.. template tag:: static_placeholder

static_placeholder
==================
.. versionadded:: 3.0

The static_placeholder template tag can be used anywhere in any template and is not bound to any
page or model. It needs a name and it will create a placeholder that you can fill with plugins
afterwards. The static_placeholder tag is normally used to display the same content on multiple
locations or inside of apphooks or other third party apps. Static_placeholder need to be published to
show up on live pages.

Example::

    {% load cms_tags %}

    {% static_placeholder "footer" %}


.. warning::

    Static_placeholders are not included in the undo/redo and page history pages

If you want additional content to be displayed in case the static placeholder is
empty, use the ``or`` argument and an additional ``{% endstatic_placeholder %}``
closing tag. Everything between ``{% static_placeholder "..." or %}`` and ``{%
endstatic_placeholder %}`` is rendered in the event that the placeholder has no plugins or
the plugins do not generate any output.

Example::

    {% static_placeholder "footer" or %}There is no content.{% endstatic_placeholder %}

By default, a static placeholder applies to *all* sites in a project.

If you want to make your static placeholder site-specific, so that different sites can have their
own content in it, you can add the flag ``site`` to the template tag to achieve this.

Example::

    {% static_placeholder "footer" site or %}There is no content.{% endstatic_placeholder %}

Note that the `Django "sites" framework <https://docs.djangoproject.com/en/dev/ref/contrib/sites/>`_ *is* required and ``SITE_ID``
:ref:`*must* be set <configure-django-cms>` in ``settings.py`` for this (not to mention other
aspects of django CMS) to work correctly.

.. templatetag:: render_placeholder

render_placeholder
==================

`{% render_placeholder %}` is used if you have a PlaceholderField in your own model and want
to render it in the template.

The :ttag:`render_placeholder` tag takes the following parameters:

* :class:`~cms.models.fields.PlaceholderField` instance
* ``width`` parameter for context sensitive plugins (optional)
* ``language`` keyword plus ``language-code`` string to render content in the
  specified language (optional)
* ``as`` keyword followed by ``varname`` (optional): the template tag output can
  be saved as a context variable for later use.


The following example renders the ``my_placeholder`` field from the ``mymodel_instance`` and will
render only the English (``en``) plugins:

.. code-block:: html+django

    {% load cms_tags %}

    {% render_placeholder mymodel_instance.my_placeholder language 'en' %}

.. versionadded:: 3.0.2
    This template tag supports the ``as`` argument. With this you can assign the result
    of the template tag to a new variable that you can use elsewhere in the template.

    Example::

        {% render_placeholder mymodel_instance.my_placeholder as placeholder_content %}
        <p>{{ placeholder_content }}</p>

    When used in this manner, the placeholder will not be displayed for
    editing when the CMS is in edit mode.

.. templatetag:: render_uncached_placeholder

render_uncached_placeholder
===========================

The same as :ttag:`render_placeholder`, but the placeholder contents will not be
cached or taken from the cache.

Arguments:

* :class:`~cms.models.fields.PlaceholderField` instance
* ``width`` parameter for context sensitive plugins (optional)
* ``language`` keyword plus ``language-code`` string to render content in the
  specified language (optional)
* ``as`` keyword followed by ``varname`` (optional): the template tag output can
  be saved as a context variable for later use.

Example::

    {% render_uncached_placeholder mymodel_instance.my_placeholder language 'en' %}


.. templatetag:: show_placeholder

show_placeholder
================

Displays a specific placeholder from a given page. This is useful if you want
to have some more or less static content that is shared among many pages, such
as a footer.

Arguments:

* ``placeholder_name``
* ``page_lookup`` (see `page_lookup`_ for more information)
* ``language`` (optional)
* ``site`` (optional)

Examples::

    {% show_placeholder "footer" "footer_container_page" %}
    {% show_placeholder "content" request.current_page.parent_id %}
    {% show_placeholder "teaser" request.current_page.get_root %}


.. templatetag:: show_uncached_placeholder

show_uncached_placeholder
=========================

The same as :ttag:`show_placeholder`, but the placeholder contents will not be
cached or taken from the cache.

Arguments:

- ``placeholder_name``
- ``page_lookup`` (see `page_lookup`_ for more information)
- ``language`` (optional)
- ``site`` (optional)

Example::

    {% show_uncached_placeholder "footer" "footer_container_page" %}


.. templatetag:: page_lookup

page_lookup
===========

The ``page_lookup`` argument, passed to several template tags to retrieve a
page, can be of any of the following types:

* :class:`str <basestring>`: interpreted as the ``reverse_id`` field of the desired page, which
  can be set in the "Advanced" section when editing a page.
* :class:`int`: interpreted as the primary key (``pk`` field) of the desired page
* :class:`dict`: a dictionary containing keyword arguments to find the desired page
  (for instance: ``{'pk': 1}``)
* :class:`~cms.models.Page`: you can also pass a page object directly, in which case there will
  be no database lookup.

If you know the exact page you are referring to, it is a good idea to use a
``reverse_id`` (a string used to uniquely name a page) rather than a
hard-coded numeric ID in your template. For example, you might have a help
page that you want to link to or display parts of on all pages. To do this,
you would first open the help page in the admin interface and enter an ID
(such as ``help``) under the 'Advanced' tab of the form. Then you could use
that ``reverse_id`` with the appropriate template tags::

    {% show_placeholder "right-column" "help" %}
    <a href="{% page_url "help" %}">Help page</a>

If you are referring to a page `relative` to the current page, you'll probably
have to use a numeric page ID or a page object. For instance, if you want the
content of the parent page to display on the current page, you can use::

    {% show_placeholder "content" request.current_page.parent_id %}

Or, suppose you have a placeholder called ``teaser`` on a page that, unless a
content editor has filled it with content specific to the current page, should
inherit the content of its root-level ancestor::

    {% placeholder "teaser" or %}
        {% show_placeholder "teaser" request.current_page.get_root %}
    {% endplaceholder %}


.. templatetag:: page_url


page_url
========

Displays the URL of a page in the current language.

Arguments:

- ``page_lookup`` (see `page_lookup`_ for more information)
- ``language`` (optional)
- ``site`` (optional)
- ``as var_name`` (version 3.0 or later, optional; page_url can now be used to assign the resulting
  URL to a context variable ``var_name``)


Example::

    <a href="{% page_url "help" %}">Help page</a>
    <a href="{% page_url request.current_page.parent %}">Parent page</a>

If a matching page isn't found and :setting:`django:DEBUG` is ``True``, an
exception will be raised. However, if :setting:`django:DEBUG` is ``False``, an
exception will not be raised. Additionally, if
:setting:`django:SEND_BROKEN_LINK_EMAILS` is ``True`` and you have specified
some addresses in :setting:`django:MANAGERS`, an email will be sent to those
addresses to inform them of the broken link.

.. versionadded:: 3.0
    page_url now supports the ``as`` argument. When used this way, the tag
    emits nothing, but sets a variable in the context with the specified name
    to the resulting value.

    When using the ``as`` argument PageNotFound exceptions are always
    suppressed, regardless of the setting of :setting:`django:DEBUG` and the
    tag will simply emit an empty string in these cases.

Example::

    {# Emit a 'canonical' tag when the page is displayed on an alternate url #}
    {% page_url request.current_page as current_url %}{% if current_url and current_url != request.get_full_path %}<link rel="canonical" href="{% page_url request.current_page %}">{% endif %}


.. templatetag:: page_attribute

page_attribute
==============

This template tag is used to display an attribute of the current page in the
current language.

Arguments:

- ``attribute_name``
- ``page_lookup`` (optional; see `page_lookup`_ for more
  information)

Possible values for ``attribute_name`` are: ``"title"``, ``"menu_title"``,
``"page_title"``, ``"slug"``, ``"meta_description"``, ``"changed_date"``, ``"changed_by"``
(note that you can also supply that argument without quotes, but this is
deprecated because the argument might also be a template variable).

Example::

    {% page_attribute "page_title" %}

If you supply the optional ``page_lookup`` argument, you will get the page
attribute from the page found by that argument.

Example::

    {% page_attribute "page_title" "my_page_reverse_id" %}
    {% page_attribute "page_title" request.current_page.parent_id %}
    {% page_attribute "slug" request.current_page.get_root %}

.. versionadded:: 2.3.2
    This template tag supports the ``as`` argument. With this you can assign the result
    of the template tag to a new variable that you can use elsewhere in the template.

    Example::

        {% page_attribute "page_title" as title %}
        <title>{{ title }}</title>

    It even can be used in combination with the ``page_lookup`` argument.

    Example::

        {% page_attribute "page_title" "my_page_reverse_id" as title %}
        <a href="/mypage/">{{ title }}</a>

.. templatetag:: render_plugin
.. versionadded:: 2.4

render_plugin
=============

This template tag is used to render child plugins of the current plugin and should be used inside plugin templates.

Arguments:

- ``plugin``

Plugin needs to be an instance of a plugin model.

Example::

    {% load cms_tags %}
    <div class="multicolumn">
    {% for plugin in instance.child_plugin_instances %}
        <div style="width: {{ plugin.width }}00px;">
            {% render_plugin plugin %}
        </div>
    {% endfor %}
    </div>

Normally the children of plugins can be accessed via the ``child_plugins`` attribute of plugins.
Plugins need the ``allow_children`` attribute to set to `True` for this to be enabled.

.. versionadded:: 3.0
.. templatetag:: render_plugin_block

render_plugin_block
===================

This template tag acts like the template tag ``render_model_block`` but with a
plugin instead of a model as its target. This is used to link from a block of
markup to a plugin's change form in edit/preview mode.

This is useful for user interfaces that have some plugins hidden from display
in edit/preview mode, but the CMS author needs to expose a way to edit them.
It is also useful for just making duplicate or alternate means of triggering
the change form for a plugin.

This would typically be used inside a parent-plugin’s render template. In this
example code below, there is a parent container plugin which renders a list of
child plugins inside a navigation block, then the actual plugin contents inside a
``DIV.contentgroup-items`` block. In this example, the navigation block is always shown,
but the items are only shown once the corresponding navigation element is
clicked. Adding this ``render_plugin_block`` makes it significantly more intuitive
to edit a child plugin's content, by double-clicking its navigation item in edit mode.

Arguments:

- ``plugin``

Example::

    {% load cms_tags l10n %}

    {% block section_content %}
    <div class="contentgroup-container">
      <nav class="contentgroup">
        <div class="inner">
          <ul class="contentgroup-items">{% for child in children %}
          {% if child.enabled %}
            <li class="item{{ forloop.counter0|unlocalize }}">
              {% render_plugin_block child %}
              <a href="#item{{ child.id|unlocalize }}">{{ child.title|safe }}</a>
              {% endrender_plugin_block %}
            </li>{% endif %}
          {% endfor %}
          </ul>
        </div>
      </nav>

      <div class="contentgroup-items">{% for child in children %}
        <div class="contentgroup-item item{{ child.id|unlocalize }}{% if not forloop.counter0 %} active{% endif %}">
          {% render_plugin child  %}
        </div>{% endfor %}
      </div>
    </div>
    {% endblock %}

.. templatetag:: render_model
.. versionadded:: 3.0

render_model
============

.. warning::

    ``render_model`` marks as safe the content of the rendered model
    attribute. This may be a security risk if used on fields which may contains
    non-trusted content. Be aware, and use the template tag accordingly.

``render_model`` is the way to add frontend editing to any Django model.
It both renders the content of the given attribute of the model instance and
makes it clickable to edit the related model.

If the toolbar is not enabled, the value of the attribute is rendered in the
template without further action.

If the toolbar is enabled, click to call frontend editing code is added.

By using this template tag you can show and edit page titles as well as fields in
standard django models, see :ref:`frontend-editable-fields` for examples and
further documentation.

Example:

.. code-block:: html+django

    <h1>{% render_model my_model "title" "title,abstract" %}</h1>

This will render to:

.. code-block:: html+django

    <!-- The content of the H1 is the active area that triggers the frontend editor -->
    <h1><div class="cms-plugin cms-plugin-myapp-mymodel-title-1">{{ my_model.title }}</div></h1>

**Arguments:**

* ``instance``: instance of your model in the template
* ``attribute``: the name of the attribute you want to show in the template; it
  can be a context variable name; it's possible to target field, property or
  callable for the specified model; when used on a page object this argument
  accepts the special ``titles`` value which will show the page **title**
  field, while allowing editing **title**, **menu title** and **page title**
  fields in the same form;
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor; when template tag is used on a page object this argument
  accepts the special ``changelist`` value which allows editing the pages
  **changelist** (items list);
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.
* ``filters`` (optional): a string containing chained filters to apply to the
  output content; works the same way as :ttag:`django:filter` template tag;
* ``view_url`` (optional): the name of a URL that will be reversed using the
  instance ``pk`` and the ``language`` as arguments;
* ``view_method`` (optional): a method name that will return a URL to a view;
  the method must accept ``request`` as first parameter.
* ``varname`` (optional): the template tag output can be saved as a context
  variable for later use.

.. warning::

    In this version of django CMS, the setting :setting:`CMS_UNESCAPED_RENDER_MODEL_TAGS`
    has a default value of ``True`` to provide behavior consistent with
    previous releases. However, all developers are encouraged to set this
    value to ``False`` to help prevent a range of security vulnerabilities
    stemming from HTML, Javascript, and CSS Code Injection.

.. warning::

    ``render_model`` is only partially compatible with django-hvad: using
    it with hvad-translated fields
    (say {% render_model object 'translated_field' %} return error if the
    hvad-enabled object does not exists in the current language.
    As a workaround ``render_model_icon`` can be used instead.


.. templatetag:: render_model_block
.. versionadded:: 3.0

render_model_block
==================

``render_model_block`` is the block-level equivalent of ``render_model``:

.. code-block:: html+django

    {% render_model_block my_model %}
        <h1>{{ instance.title }}</h1>
        <div class="body">
            {{ instance.date|date:"d F Y" }}
            {{ instance.text }}
        </div>
    {% endrender_model_block %}

This will render to:

.. code-block:: html+django

    <!-- This whole block is the active area that triggers the frontend editor -->
    <div class="cms-plugin cms-plugin-myapp-mymodel-1">
        <h1>{{ my_model.title }}</h1>
        <div class="body">
            {{ my_model.date|date:"d F Y" }}
            {{ my_model.text }}
        </div>
    </div>

In the block the ``my_model`` is aliased as ``instance`` and every attribute and
method is available; also template tags and filters are available in the block.

.. warning::

    If the ``{% render_model_block %}`` contains template tags or template code that rely on or
    manipulate context data that the ``{% render_model_block %}`` also makes use of, you may
    experience some unexpected effects. Unless you are sure that such conflicts will not occur
    it is advised to keep the code within a ``{% render_model_block %}`` as simple and short as
    possible.

**Arguments:**

* ``instance``: instance of your model in the template
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor; when template tag is used on a page object this argument
  accepts the special ``changelist`` value which allows editing the pages
  **changelist** (items list);
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.
* ``view_url`` (optional): the name of a URL that will be reversed using the
  instance ``pk`` and the ``language`` as arguments;
* ``view_method`` (optional): a method name that will return a URL to a view;
  the method must accept ``request`` as first parameter.
* ``varname`` (optional): the template tag output can be saved as a context
  variable for later use.

.. warning::

    In this version of django CMS, the setting :setting:`CMS_UNESCAPED_RENDER_MODEL_TAGS`
    has a default value of ``True`` to provide behavior consistent with
    previous releases. However, all developers are encouraged to set this
    value to ``False`` to help prevent a range of security vulnerabilities
    stemming from HTML, Javascript, and CSS Code Injection.

.. templatetag:: render_model_icon
.. versionadded:: 3.0


render_model_icon
=================

``render_model_icon`` is intended for use where the relevant object attribute
is not available for user interaction (for example, already has a link on it,
think of a title in a list of items and the titles are linked to the object
detail view); when in edit mode, it renders an **edit** icon, which will trigger
the editing change form for the provided fields.


.. code-block:: html+django

    <h3><a href="{{ my_model.get_absolute_url }}">{{ my_model.title }}</a> {% render_model_icon my_model %}</h3>

It will render to something like:

.. code-block:: html+django

    <h3>
        <a href="{{ my_model.get_absolute_url }}">{{ my_model.title }}</a>
        <div class="cms-plugin cms-plugin-myapp-mymodel-1 cms-render-model-icon">
            <!-- The image below is the active area that triggers the frontend editor -->
            <img src="/static/cms/img/toolbar/render_model_placeholder.png">
        </div>
    </h3>

.. note::

        Icon and position can be customised via CSS by setting a background
        to the ``.cms-render-model-icon img`` selector.

**Arguments:**

* ``instance``: instance of your model in the template
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor; when template tag is used on a page object this argument
  accepts the special ``changelist`` value which allows editing the pages
  **changelist** (items list);
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.
* ``view_url`` (optional): the name of a URL that will be reversed using the
  instance ``pk`` and the ``language`` as arguments;
* ``view_method`` (optional): a method name that will return a URL to a view;
  the method must accept ``request`` as first parameter.
* ``varname`` (optional): the template tag output can be saved as a context
  variable for later use.

.. warning::

    In this version of django CMS, the setting :setting:`CMS_UNESCAPED_RENDER_MODEL_TAGS`
    has a default value of ``True`` to provide behavior consistent with
    previous releases. However, all developers are encouraged to set this
    value to ``False`` to help prevent a range of security vulnerabilities
    stemming from HTML, Javascript, and CSS Code Injection.

.. templatetag:: render_model_add
.. versionadded:: 3.0


render_model_add
================

``render_model_add`` is similar to ``render_model_icon`` but it will enable to
create instances of the given instance class; when in edit mode, it renders an
**add** icon, which will trigger the editing add form for the provided model.


.. code-block:: html+django

    <h3><a href="{{ my_model.get_absolute_url }}">{{ my_model.title }}</a> {% render_model_add my_model %}</h3>

It will render to something like:

.. code-block:: html+django

    <h3>
        <a href="{{ my_model.get_absolute_url }}">{{ my_model.title }}</a>
        <div class="cms-plugin cms-plugin-myapp-mymodel-1 cms-render-model-add">
            <!-- The image below is the active area that triggers the frontend editor -->
            <img src="/static/cms/img/toolbar/render_model_placeholder.png">
        </div>
    </h3>

.. note::

        Icon and position can be customised via CSS by setting a background
        to the ``.cms-render-model-add img`` selector.

**Arguments:**

* ``instance``: instance of your model, or model class to be added
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor;
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.
* ``view_url`` (optional): the name of a url that will be reversed using the
  instance ``pk`` and the ``language`` as arguments;
* ``view_method`` (optional): a method name that will return a URL to a view;
  the method must accept ``request`` as first parameter.
* ``varname`` (optional): the template tag output can be saved as a context
  variable for later use.

.. warning::

    In this version of django CMS, the setting :setting:`CMS_UNESCAPED_RENDER_MODEL_TAGS`
    has a default value of ``True`` to provide behavior consistent with
    previous releases. However, all developers are encouraged to set this
    value to ``False`` to help prevent a range of security vulnerabilities
    stemming from HTML, Javascript, and CSS Code Injection.

.. warning::

    If passing a class, instead of an instance, and using ``view_method``,
    please bear in mind that the method will be called over an **empty instance**
    of the class, so attributes are all empty, and the instance does not
    exists on the database.


.. _django-hvad: https://github.com/kristianoellegaard/django-hvad

.. templatetag:: render_model_add_block
.. versionadded:: 3.1

render_model_add_block
======================

``render_model_add_block`` is similar to ``render_model_add`` but instead of
emitting an icon that is linked to the add model form in a modal dialog, it
wraps arbitrary markup with the same "link". This allows the developer to create
front-end editing experiences better suited to the project.

All arguments are identical to ``render_model_add``, but the template tag is used
in two parts to wrap the markup that should be wrapped.

.. code-block:: html+django

    {% render_model_add_block my_model_instance %}<div>New Object</div>{% endrender_model_add_block %}


It will render to something like:

.. code-block:: html+django

    <div class="cms-plugin cms-plugin-myapp-mymodel-1 cms-render-model-add">
      <div>New Object</div>
    </div>


.. warning::

    You **must** pass an *instance* of your model as instance parameter. The
    instance passed could be an existing models instance, or one newly created
    in your view/plugin. It does not even have to be saved, it is introspected
    by the template tag to determine the desired model class.


**Arguments:**

* ``instance``: instance of your model in the template
* ``edit_fields`` (optional): a comma separated list of fields editable in the
  popup editor;
* ``language`` (optional): the admin language tab to be linked. Useful only for
  `django-hvad`_ enabled models.
* ``view_url`` (optional): the name of a URL that will be reversed using the
  instance ``pk`` and the ``language`` as arguments;
* ``view_method`` (optional): a method name that will return a URL to a view;
  the method must accept ``request`` as first parameter.
* ``varname`` (optional): the template tag output can be saved as a context
  variable for later use.

.. _django-hvad: https://github.com/kristianoellegaard/django-hvad


.. templatetag:: page_language_url


page_language_url
=================

Returns the URL of the current page in an other language::

    {% page_language_url de %}
    {% page_language_url fr %}
    {% page_language_url en %}

If the current URL has no CMS Page and is handled by a navigation extender and
the URL changes based on the language, you will need to set a ``language_changer``
function with the ``set_language_changer`` function in ``menus.utils``.

For more information, see :doc:`/topics/i18n`.

.. templatetag:: language_chooser


language_chooser
================

The ``language_chooser`` template tag will display a language chooser for the
current page. You can modify the template in ``menu/language_chooser.html`` or
provide your own template if necessary.

Example::

    {% language_chooser %}

or with custom template::

    {% language_chooser "myapp/language_chooser.html" %}

The language_chooser has three different modes in which it will display the
languages you can choose from: "raw" (default), "native", "current" and "short".
It can be passed as the last argument to the ``language_chooser tag`` as a string.
In "raw" mode, the language will be displayed like its verbose name in the
settings. In "native" mode the languages are displayed in their actual language
(eg. German will be displayed "Deutsch", Japanese as "日本語" etc). In "current"
mode the languages are translated into the current language the user is seeing
the site in (eg. if the site is displayed in German, Japanese will be displayed
as "Japanisch"). "Short" mode takes the language code (eg. "en") to display.

If the current URL has no CMS Page and is handled by a navigation extender and
the URL changes based on the language, you will need to set a ``language_changer``
function with the ``set_language_changer`` function in ``menus.utils``.

For more information, see :doc:`/topics/i18n`.

*********************
Toolbar template tags
*********************

.. highlightlang:: html+django

The ``cms_toolbar`` template tag is included in the ``cms_tags`` library and will add the
required CSS and javascript to the sekizai blocks in the base template. The template tag
has to be placed after the ``<body>`` tag and before any ``{% cms_placeholder %}`` occurrences
within your HTML.

Example::

    <body>
    {% cms_toolbar %}
    {% placeholder "home" %}
    ...


.. note::

    Be aware that you can not surround the cms_toolbar tag with block tags.
    The toolbar tag will render everything below it to collect all plugins and placeholders, before
    it renders itself. Block tags interfere with this.


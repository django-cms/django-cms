.. _colorscheme:

##########################################
Color schemes (light/dark) with django CMS
##########################################

.. important::

    These notes about the color scheme apply only to the **django CMS admin and editing
    interfaces**. The visitor-facing published site is **wholly independent** of this, and the
    responsibility of the site developer.

    The admin interfaces will only reflect the described behavior if the package
    ``djangocms-admin-style`` is installed (version 3.2 or later). If it is not installed the admin
    interface is managed by your underlying Django installation which usually
    uses the browser's color scheme.

************************
Setting the color scheme
************************

Django CMS' default color scheme is ``"light"``. To change the color scheme use the ``CMS_COLOR_SCHEME``
setting in your project's ``setting.py``:

``CMS_COLOR_SCHEME = "light"``
    This is the default appearance and shows the interface with dark text on white background.

``CMS_COLOR_SCHEME = "dark"``
    This so-called dark mode show light text on dark background.

``CMS_COLOR_SCHEME = "auto"``
    The auto mode chooses either light or dark color scheme based on the browser or
    operating system setting of the user.

.. hint::

    If you plan to fix the color scheme to either light or dark, add a corresponding
    ``data-theme`` attribute to the ``html`` tag in your base template, e.g.

    .. code-block::

        <html data-theme="light">

    This will pin the color scheme early when loading pages and avoid potential
    flickering if the browser preference differs from the ``CMS_COLOR_SCHEME``
    setting.

.. versionchanged:: 3.11.4

    Before version 3.11.4 the color scheme was set by ``data-color-scheme``. Since version 3.11.4 django CMS uses ``data-theme`` just as Django since version 4.2.


.. important::

    Not all plugin admin interfaces might support a dark color scheme, especially
    if plugin forms contain custom widgets.

**********************************
Toggle button for the color scheme
**********************************

Adding the setting ``CMS_COLOR_SCHEME_TOGGLE = True`` to the project's ``settings.py`` will add a toggle icon (sun/moon) to the toolbar allowing a user to switch their color scheme for their session.


******************************************
Make your own admin css color scheme aware
******************************************

Plugin forms or any admin forms use Django's admin app which itself supports light and dark color schemes. djangocms-admin-style introduces django CMS' color scheme to the admin app. Just as Django does, djangocms-admin-style defines css variables for frequent colors.

We recommend to write at least your reusable apps in a way which allows  them to respect the color scheme with djangocms-admin-style and with Django's admin style.

Here's some recommendations for making your app work as seamlessly as possible:

* Try avoiding using ``color``, ``background-color``, or other color styles where possible and meaningful.
* If necessary use as few as possible standard django CMS colors (preferably from the list below with plain Django fallback colors)
* Use the following pattern: ``var(--dca-color-var, var(--fallback-color-var, #xxxxxx))`` where ``#xxxxxx`` represents the light version of the color. This tries django CMS color scheme first and falls back to Django color scheme if djangocms-admin-style is not available.
* Avoid media queries like ``@media (prefers-color-scheme: dark)`` since they would ignore forced settings to light or dark.


The admin frontend pulls the style from django admin styles and - if present - from djangocms-admin-style. Django itself also uses css variables to implement admin mode, these can be used as dark mode-aware fall-back colors.

Here's a table of django CMS' css color variables and their Django fallbacks:

=============================== =========== ======================= ===========
Variable name                   Color       Fallback                Color
=============================== =========== ======================= ===========
``--dca-white``                 ``#ffffff`` ``--body-bg``           ``#ffffff``
``--dca-gray``                  ``#666``    ``--body-quiet-color``  ``#666``
``--dca-gray-lightest``         ``#f2f2f2`` ``--darkened-bg``       ``#f8f8f8``
``--dca-gray-lighter``          ``#ddd``    ``--border-color``      ``#ccc``
``--dca-gray-light``            ``#999``    ``--close-button-bg``   ``#888``
``--dca-gray-darker``           ``#454545``
``--dca-gray-darkest``          ``#333``
``--dca-gray-super-lightest``   ``#f7f7f7``
``--dca-primary``               ``#00bbff`` ``--primary``           ``#79aec8``
``--dca-black``                 ``#000``    ``--body-fg``           ``#303030``
=============================== =========== ======================= ===========

This leaves these recommendation for color scheme dependent colors:

.. code-block::

    white:          var(--dca-white, var(--body-bg, #fff))
    gray:           var(--dca-gray, var(--body-quiet-color, #666))
    gray-lightest:  var(--dca-gray-lightest, var(--darkened-bg, #f2f2f2))
    gray-lighter    var(--dca-gray-lighter, var(--border-color, #ddd))
    gray-light:     var(--dca-gray-lightest, var(--darkened-bg, #f2f2f2))
    gray-primary:   var(--dca-primary, var(--primary, #0bf))
    black:          var(--dca-black, var(--body-fg), #000))

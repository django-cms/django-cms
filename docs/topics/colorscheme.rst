.. _colorscheme:

##########################################
Color schemes (light/dark) with django CMS
##########################################

.. important::

    These notes about the color scheme apply only to the **django CMS admin and editing
    interfaces**. The visitor-facing published site is **wholly independent** of this, and the
    responsibility of the site developer.

    The admin interfaces will only reflect the described behavior if the package
    ``djangocms-admin-style`` is installed (version XXX or later). If it is not installed the admin
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
    ``data-color-scheme`` attribute to the ``html`` tag in your base template, e.g.

    .. code-block::

        <html data-color-scheme="light">

    This will pin the color scheme early when loading pages and avoid potential
    flickering if the browser preference differs from the ``CMS_COLOR_SCHEME``
    setting.


.. important::

    Not all plugin admin interfaces might support a dark color scheme, especially
    if plugin forms contain custom widgets. See XXXX on how to make your widgets
    compatible with django CMS' color scheme support.

**********************************
Toggle button for the color scheme
**********************************

Adding the setting ``CMS_COLOR_SCHEME_TOGGLE = True`` to the project's ``settings.py``
will add a toggle icon (sun/moon) to the toolbar allowing a user to switch their
color scheme for their session.



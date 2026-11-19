########################################
How to use a Content Security Policy
########################################

A Content Security Policy (CSP) tells the browser which scripts and stylesheets it is
allowed to run. The strictest practical policy is a *nonce-based* one: the server
generates a random token for every response, puts it in the
``Content-Security-Policy`` header, and repeats it on every asset it trusts. Anything
without the token -- including markup injected by an attacker -- is refused.

django CMS renders the nonce on all assets it emits itself, so the admin, the page
tree, the toolbar and the wizards keep working under such a policy.

.. versionadded:: 5.1
    Nonce support requires Django 6.1 or later. On Django 5.2 and 6.0 the templates
    render exactly as before, without a ``nonce`` attribute.


******
Set-up
******

Django 6.1 ships CSP support out of the box. Three pieces are needed:

#. Add the middleware that generates the nonce and writes the header::

    MIDDLEWARE = [
        "django.middleware.csp.ContentSecurityPolicyMiddleware",
        ...
    ]

#. Add the context processor that makes the nonce available to templates::

    TEMPLATES = [
        {
            ...
            "OPTIONS": {
                "context_processors": [
                    ...
                    "django.template.context_processors.csp",
                ],
            },
        },
    ]

#. Declare a policy that uses the nonce placeholder::

    from django.utils.csp import CSP

    SECURE_CSP = {
        "default-src": [CSP.SELF],
        "script-src": [CSP.SELF, CSP.NONCE],
        "style-src": [CSP.SELF, CSP.NONCE],
    }

``CSP.NONCE`` is replaced with the request's nonce when the header is built. See
`Django's CSP how-to <https://docs.djangoproject.com/en/6.1/howto/csp/>`_ for the
full picture.

.. note::
    Start with ``SECURE_CSP_REPORT_ONLY`` instead of ``SECURE_CSP``. The browser then
    reports violations without blocking anything, which lets you find assets from your
    own templates or from third-party apps that do not carry the nonce yet.


*******************************
Nonces in your own templates
*******************************

Any script or stylesheet **you** add has to carry the nonce as well. Django 6.1
registers a built-in ``{% csp_nonce_attr %}`` tag for that, but it does not exist on
Django 5.2 and 6.0. If your project or add-on supports those versions too, load
django CMS' cross-version version of the tag instead:

.. code-block:: html+django

    {% load cms_static %}

    <script src="{% static 'myapp/js/app.js' %}" {% csp_nonce_attr %}></script>
    <link rel="stylesheet" href="{% static 'myapp/css/app.css' %}" {% csp_nonce_attr %}>
    <style {% csp_nonce_attr %}>...</style>

The tag renders ``nonce="..."`` when a nonce is available and nothing at all
otherwise, so a single template works on every supported Django version.

Form and widget media take the nonce as an argument:

.. code-block:: html+django

    {% csp_nonce_attr form.media %}

If you need the assets one at a time -- for example to wrap each of them in a
separate sekizai ``{% addtoblock %}``, the way the toolbar does -- use
``{% render_media_assets %}``:

.. code-block:: html+django

    {% render_media_assets form.media "css" as css_assets %}
    {% for css in css_assets %}
        {% addtoblock "css" %}{{ css }}{% endaddtoblock %}
    {% endfor %}

The second argument is either ``"css"`` or ``"js"``.


**********************************
What does *not* need a nonce
**********************************

``<script type="application/json">`` data blocks -- such as the toolbar's
``cms-config-json`` element and the JSON emitted by ``json_script`` -- carry **no**
nonce, and must not be given one. Browsers never execute them, so CSP never checks
them; this matches Django's own ``json_script()``.

``<link rel="icon">`` and other non-stylesheet links are governed by ``img-src``
rather than ``style-src`` and take no nonce either.


********************
Caching and nonces
********************

A nonce is valid for exactly one response. Never store a rendered page that contains
one in a shared cache, or the browser will reject the assets of every later visitor.

django CMS' own page cache is safe here: it only serves cached responses to anonymous
visitors who see no toolbar, so no nonce-bearing markup ever enters it. Take the same
care with any caching you add yourself, and be aware that Django's
:class:`~django.middleware.cache.UpdateCacheMiddleware` does not know about nonces.


*******************
Inline JavaScript
*******************

django CMS itself contains no inline JavaScript and no inline event handlers, so a
policy without ``'unsafe-inline'`` needs no exceptions for the CMS. If your own
templates still use ``onclick="..."`` attributes or inline ``<script>`` blocks, move
them into static files -- a nonce cannot rescue inline event handlers, which are only
allowed by ``'unsafe-inline'`` or ``'unsafe-hashes'``.

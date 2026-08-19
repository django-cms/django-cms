from django import template
from django.templatetags.static import StaticNode

from cms.utils.urlutils import static_with_version

try:
    # Django >= 6.1 ships Content Security Policy support. ``nonce_attr`` renders
    # ``nonce="..."`` when the CSP context processor put a nonce in the context,
    # and an empty string otherwise.
    from django.utils.csp import CONTEXT_KEY as CSP_CONTEXT_KEY, nonce_attr as _nonce_attr

    CSP_NONCE_SUPPORTED = True
except ImportError:  # Django < 6.1
    CSP_NONCE_SUPPORTED = False
    CSP_CONTEXT_KEY = "csp_nonce"

    def _nonce_attr(context, media=None):
        return media.render() if media is not None else ""


register = template.Library()


@register.tag('static_with_version')
def do_static_with_version(parser, token):
    """
    Joins the given path with the STATIC_URL setting
    and appends the CMS version as a GET parameter.

    Usage::
        {% static_with_version path [as varname] %}
    Examples::
        {% static_with_version "myapp/css/base.css" %}
        {% static_with_version variable_with_path %}
        {% static_with_version "myapp/css/base.css" as admin_base_css %}
        {% static_with_version variable_with_path as varname %}
    """
    return StaticWithVersionNode.handle_token(parser, token)


class StaticWithVersionNode(StaticNode):

    def url(self, context):
        path = self.path.resolve(context)
        path_with_version = static_with_version(path)

        return self.handle_simple(path_with_version)


@register.simple_tag(takes_context=True)
def csp_nonce_attr(context, media=None):
    """Render the request's Content Security Policy nonce.

    This is a cross-version stand-in for Django 6.1's built-in tag of the same
    name. Django 6.1 registers ``csp_nonce_attr`` as a built-in, so loading
    ``cms_static`` shadows it with this identical implementation; on Django 5.2
    and 6.0, where the built-in does not exist, the fallback renders nothing.

    Usage::

        <script src="..." {% csp_nonce_attr %}></script>
        {% csp_nonce_attr form.media %}

    Without an argument it renders ``nonce="..."`` when a nonce is available and
    an empty string otherwise. Given a :class:`~django.forms.Media` object it
    renders that media, adding the nonce to every element.

    Note that non-executable ``<script type="application/json">`` data blocks
    must *not* carry a nonce: browsers never run them, so CSP does not check
    them, and Django's own ``json_script`` leaves them bare.
    """
    return _nonce_attr(context, media)


@register.simple_tag(takes_context=True)
def render_media_assets(context, media, media_type):
    """Render each asset of ``media`` separately, carrying the CSP nonce.

    ``{% csp_nonce_attr media %}`` renders a whole :class:`~django.forms.Media`
    object as one blob. Callers that need to place assets individually -- the
    toolbar wraps every asset in its own sekizai ``{% addtoblock %}`` so that
    sekizai can deduplicate per file -- use this instead::

        {% render_media_assets cms_toolbar.media "css" as toolbar_css %}
        {% for css in toolbar_css %}
            {% addtoblock "css" %}{{ css }}{% endaddtoblock %}
        {% endfor %}

    ``media_type`` is either ``"css"`` or ``"js"``.
    """
    if media_type not in ("css", "js"):
        raise template.TemplateSyntaxError(
            f"render_media_assets expects a media type of 'css' or 'js', got {media_type!r}"
        )

    renderer = getattr(media, f"render_{media_type}")

    if CSP_NONCE_SUPPORTED:
        nonce = context.get(CSP_CONTEXT_KEY)
        if nonce is not None:
            return list(renderer(attrs={"nonce": nonce}))
    return list(renderer())

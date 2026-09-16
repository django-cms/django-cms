"""The toolbar's own templatetag: ``{% cms_toolbar %}``.

Registered by :mod:`cms.templatetags.cms_tags`; see that module for why the
library stays where it is.
"""

from classytags.arguments import Argument
from classytags.core import Options
from sekizai.templatetags.sekizai_tags import RenderBlock, SekizaiParser

from cms.toolbar.utils import get_toolbar_from_request


class CMSToolbar(RenderBlock):
    name = "cms_toolbar"

    options = Options(
        Argument("name", required=False),  # just here so sekizai thinks this is a RenderBlock
        parser_class=SekizaiParser,
    )

    def render_tag(self, context, name, nodelist):
        request = context.get("request")

        if not request:
            return nodelist.render(context)

        toolbar = get_toolbar_from_request(request)

        if toolbar and toolbar.show_toolbar:
            toolbar.init_toolbar(request)
            return toolbar.render_with_structure(context, nodelist)
        return nodelist.render(context)

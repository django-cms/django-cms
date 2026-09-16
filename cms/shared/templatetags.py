"""Templatetag pieces that belong to no container.

``{% cms_admin_url %}``, plus two classytags helpers with no CMS semantics of
their own that several containers' tags need. Registered by
:mod:`cms.templatetags.cms_tags`.
"""

from classytags.arguments import Argument, MultiKeywordArgument, MultiValueArgument
from classytags.core import Options
from classytags.helpers import AsTag
from classytags.values import StringValue
from django.utils.translation import override

from cms.utils.urlutils import admin_reverse

#: Sentinel for "no value given", distinct from ``None``.
NULL = object()


class EmptyListValue(list, StringValue):
    """
    A list of template variables for easy resolving
    """

    def __init__(self, value=NULL):
        list.__init__(self)
        if value is not NULL:
            self.append(value)

    def resolve(self, context):
        resolved = [item.resolve(context) for item in self]
        return self.clean(resolved)


class MultiValueArgumentBeforeKeywordArgument(MultiValueArgument):
    sequence_class = EmptyListValue

    def parse(self, parser, token, tagname, kwargs):
        if "=" in token:
            if self.name not in kwargs:
                kwargs[self.name] = self.sequence_class()
            return False
        return super().parse(parser, token, tagname, kwargs)

class CMSAdminURL(AsTag):
    name = "cms_admin_url"
    options = Options(
        Argument("viewname"),
        MultiValueArgumentBeforeKeywordArgument("args", required=False),
        MultiKeywordArgument("kwargs", required=False),
        "as",
        Argument("varname", resolve=False, required=False),
    )

    def get_value(self, context, viewname, args, kwargs):
        request = context.get("request", None)
        if request and hasattr(request, "toolbar"):
            with override(request.toolbar.request.toolbar.toolbar_language):
                return admin_reverse(viewname, args=args, kwargs=kwargs)
        return admin_reverse(viewname, args=args, kwargs=kwargs)

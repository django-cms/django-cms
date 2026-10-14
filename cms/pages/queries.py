"""Read services for pages, without an HttpRequest.

The page counterpart of :mod:`cms.core.queries`: what a REST API or an MCP
server needs to find pages and their content, decided by the same rules as the
site. Every read takes an :class:`~cms.shared.operations.OperationContext` and
an ``admin`` flag:

* ``admin=False`` (the default) reads what the site shows: the published
  content (``PageContent.objects``; with djangocms-versioning, the published
  version), of pages the user may view -- view restrictions, ``CMS_PUBLIC_FOR``
  and ``login_required`` applied.
* ``admin=True`` reads what an editor sees: the current content including
  drafts (``PageContent.admin_manager``), for active staff users, of pages they
  may view.

A page or content the user may not read raises its ``DoesNotExist``, exactly as
if it did not exist. Lists simply leave it out. Lists and trees read their
pages, contents and view restrictions in a fixed number of queries, however many
pages there are, and leave page types out.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial

from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.models import Site
from django.utils.translation import gettext_lazy as _lazy

from cms.core.queries import get_source
from cms.models import Page, PageContent, PageUrl
from cms.operations import Argument, Query, Result, register_query
from cms.pages.models.managers import search_page_contents
from cms.permissions.page_permissions import filter_viewable_page_contents
from cms.shared.lookups import register_lookup
from cms.utils.i18n import get_fallback_languages

__all__ = [
    "PageNode",
    "get_page",
    "get_page_by_path",
    "get_page_content",
    "get_page_contents",
    "get_page_tree",
    "search_pages",
]


def _user(context):
    return context.user if context.user is not None else AnonymousUser()


def _may_edit(user) -> bool:
    return bool(getattr(user, "is_active", False) and getattr(user, "is_staff", False))


def _contents(admin: bool):
    """The page contents a mode reads: current ones including drafts, or the published ones."""
    return PageContent.admin_manager.current_content() if admin else PageContent.objects.all()


def _visible(user, page_contents, site, admin: bool) -> list:
    """Those of ``page_contents`` whose page ``user`` may read in the mode."""
    if admin and not _may_edit(user):
        return []
    visible = filter_viewable_page_contents(user, page_contents, site)
    if not admin and not user.is_authenticated:
        # Not a view permission: the page view enforces it (cms.views.details).
        visible = [content for content in visible if not content.page.login_required]
    return visible


def _languages(site_id: int, language: str, fallback: bool) -> list[str]:
    return [language, *get_fallback_languages(language, site_id=site_id)] if fallback else [language]


def _hidden(model):
    return model.DoesNotExist(f"{model._meta.object_name} matching query does not exist.")


# -- single pages ----------------------------------------------------------------


def _readable_page(page: Page, context, admin: bool) -> Page:
    """``page`` if it has content in the mode and the user may read it."""
    user = _user(context)
    contents = list(_contents(admin).filter(page=page).select_related("page")[:1])
    if not contents or not _visible(user, contents, page.site, admin):
        raise _hidden(Page)
    return page


def get_page(pk, context, *, admin: bool = False) -> Page:
    """The page with primary key ``pk``, if it has content in the mode and the user may read it.

    :raises Page.DoesNotExist: if there is none, or the user may not read it.
    """
    return _readable_page(Page.objects.select_related("site").get(pk=pk), context, admin)


def get_page_by_path(
    site: Site, path: str, context, *, language: str | None = None, admin: bool = False
) -> Page:
    """The page of ``site`` at ``path`` (``"about/team"``; ``""`` for the home page).

    Paths are per language, so two pages may share one in different languages:
    the page with ``path`` in ``language`` is preferred, then the page whose URL
    with that path was created first. The page's URLs with ``path`` are cached
    on it (``page.urls_cache``) -- its own only.

    :raises Page.DoesNotExist: if there is none, or the user may not read it.
    """
    page_urls = list(
        PageUrl.objects.get_for_site(site).filter(path=path.strip("/")).select_related("page").order_by("pk")
    )
    if not page_urls:
        raise _hidden(Page)
    chosen = next((url for url in page_urls if url.language == language), page_urls[0])
    page = chosen.page
    page.urls_cache = {url.language: url for url in page_urls if url.page_id == page.pk}
    return _readable_page(page, context, admin)


def get_page_content(
    page: Page, language: str, context, *, admin: bool = False, fallback: bool = True
) -> PageContent:
    """The content of ``page`` in ``language``, or -- with ``fallback`` -- in its first fallback language.

    The fallback languages are the site's (``CMS_LANGUAGES``), as the page view
    uses them. The content's ``language`` says which one was found.

    The content is read through the mode's manager, never from the page's
    ``page_content_cache`` or ``admin_content_cache``: whoever filled those
    decided what is in them, and a draft there must not become a published read.

    :raises PageContent.DoesNotExist: if there is none, or the user may not read it.
    """
    languages = _languages(page.site_id, language, fallback)
    candidates = _contents(admin).filter(page_id=page.pk, language__in=languages).select_related("page__site")
    contents = _one_per_page(candidates, languages)
    if not contents or not _visible(_user(context), contents, contents[0].page.site, admin):
        raise _hidden(PageContent)
    return contents[0]


# -- lists, trees and search -------------------------------------------------------


def _one_per_page(page_contents, languages: list[str]) -> list[PageContent]:
    """The best content per page, by the order of ``languages``, in page tree order."""
    best = {}
    for content in page_contents:
        current = best.get(content.page_id)
        if current is None or languages.index(content.language) < languages.index(current.language):
            best[content.page_id] = content
    return sorted(best.values(), key=lambda content: content.page.path)


def get_page_contents(
    site: Site, language: str, context, *, admin: bool = False, fallback: bool = True
) -> list[PageContent]:
    """The content of every page of ``site`` the user may read, one per page, in page tree order.

    Each page's content is in ``language`` or -- with ``fallback`` -- its first
    fallback language; pages with neither are left out. Page types are left out.
    """
    languages = _languages(site.pk, language, fallback)
    contents = (
        _contents(admin)
        .filter(page__site=site, page__is_page_type=False, language__in=languages)
        .select_related("page")
    )
    return _visible(_user(context), _one_per_page(contents, languages), site, admin)


@dataclass
class PageNode:
    """A page in the page tree: its content and the nodes of its children."""

    content: PageContent
    children: list[PageNode] = field(default_factory=list)

    @property
    def page(self) -> Page:
        return self.content.page


def get_page_tree(
    site: Site, language: str, context, *, admin: bool = False, fallback: bool = True
) -> list[PageNode]:
    """The pages of :func:`get_page_contents` as a tree: the root nodes, children in tree order.

    A page whose parent the user may not read, or which has no content in the
    language, is left out with its descendants, as in the menu.
    """
    nodes = {}
    roots = []
    for content in get_page_contents(site, language, context, admin=admin, fallback=fallback):
        node = nodes[content.page_id] = PageNode(content)
        parent_id = content.page.parent_id
        if parent_id is None:
            roots.append(node)
        elif parent_id in nodes:
            nodes[parent_id].children.append(node)
    return roots


def search_pages(site: Site, q: str, language: str, context, *, admin: bool = False) -> list[PageContent]:
    """The content in ``language`` of the pages of ``site`` matching ``q``, in page tree order.

    Matches as :meth:`Page.objects.search <cms.pages.models.managers.PageManager.search>`
    does -- the title, or the ``search_fields`` of the content's plugins, in
    ``language``, case-insensitively -- but searches the content of the mode:
    the public content, or with ``admin=True`` the editor's, drafts included.
    Only pages the user may read are returned; page types are left out.
    """
    if not q:
        return []
    contents = _contents(admin).filter(page__site=site, page__is_page_type=False, language=language)
    matching = search_page_contents(contents, q, language).select_related("page")
    return _visible(_user(context), sorted(matching, key=lambda content: content.page.path), site, admin)


# -- lookups ------------------------------------------------------------------------


def _get_site(pk, context, *, admin: bool = False) -> Site:
    # Sites are the frame of every page read, not content: anyone may name one.
    return Site.objects.get(pk=pk)


register_lookup("cms.page", get_page)
register_lookup("cms.pagecontent", partial(get_source, "cms.pagecontent"))
register_lookup("sites.site", _get_site)


# -- query registry -------------------------------------------------------------------
# Summaries are shown to people and translated; descriptions are read by API
# schemas and assistant tool definitions and stay plain English.

_PK = (int, str)
_BOTH = ("published", "editing")
_SITE = Argument("site", model="sites.Site", description="The site.")
_LANGUAGE = Argument("language", type=str, description="The language of the content.")
_FALLBACK = Argument(
    "fallback",
    type=bool,
    required=False,
    description="Use the site's fallback languages for a page without content in the language (default true).",
)
_CONTENTS = Result(
    model="cms.PageContent", many=True, description="One content per page, in page tree order; content.page is set."
)

for _declaration in (
    Query(
        "get_page",
        summary=_lazy("A page"),
        description="A page by its id. Not found if it has no content to read or the user may not view it.",
        service=get_page,
        arguments=(Argument("pk", type=_PK, description="The page's id."),),
        returns=Result(model="cms.Page", description="The page."),
        modes=_BOTH,
    ),
    Query(
        "get_page_by_path",
        summary=_lazy("A page by its path"),
        description=(
            'A page of a site by its URL path: "about/team", or "" for the home page. '
            "Not found if there is no such page or the user may not view it."
        ),
        service=get_page_by_path,
        arguments=(
            _SITE,
            Argument("path", type=str, description="The page's path, without the language prefix."),
            Argument(
                "language",
                type=str,
                required=False,
                description="Prefer the page with this path in this language; paths are per language.",
            ),
        ),
        returns=Result(model="cms.Page", description="The page."),
        modes=_BOTH,
    ),
    Query(
        "get_page_content",
        summary=_lazy("A page's content"),
        description=(
            "The content of a page in a language, or in the site's first fallback language that has content. "
            "Its language field says which. Not found if there is none or the user may not view the page."
        ),
        service=get_page_content,
        arguments=(
            Argument("page", model="cms.Page", description="The page."),
            _LANGUAGE,
            _FALLBACK,
        ),
        returns=Result(model="cms.PageContent", description="The content."),
        modes=_BOTH,
    ),
    Query(
        "get_page_contents",
        summary=_lazy("Pages of a site"),
        description=(
            "The content of every page of a site the user may view, one per page, in page tree order. "
            "Pages without content in the language or a fallback language, and page types, are left out."
        ),
        service=get_page_contents,
        arguments=(_SITE, _LANGUAGE, _FALLBACK),
        returns=_CONTENTS,
        modes=_BOTH,
    ),
    Query(
        "get_page_tree",
        summary=_lazy("Page tree of a site"),
        description=(
            "The pages of a site the user may view, as a tree: the root pages, each with its children. "
            "A page whose parent is left out is left out with its descendants."
        ),
        service=get_page_tree,
        arguments=(_SITE, _LANGUAGE, _FALLBACK),
        returns=Result(
            many=True,
            fields={
                "content": Result(model="cms.PageContent", description="The page's content; content.page is set."),
                "children": Result(type=list, description="The child nodes, of the same shape, in tree order."),
            },
            description="The root nodes.",
        ),
        modes=_BOTH,
    ),
    Query(
        "search_pages",
        summary=_lazy("Search pages"),
        description=(
            "The content of the pages of a site whose title, or the searchable fields of whose plugins, "
            "contain the search term in the language, case-insensitively. In page tree order; pages the user "
            "may not view and page types are left out."
        ),
        service=search_pages,
        arguments=(_SITE, Argument("q", type=str, description="The search term."), _LANGUAGE),
        returns=_CONTENTS,
        modes=_BOTH,
    ),
):
    register_query(_declaration)
del _declaration

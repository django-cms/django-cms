"""Serialize page mutations before preparing or validating their inputs."""

from contextlib import contextmanager
from functools import wraps
from inspect import signature

from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.models import F
from django.utils.translation import gettext_lazy as _


class PageUrlConflict(IntegrityError):
    """A URL collision detected by the model before writing to the database."""


def _is_url_conflict(error):
    cause = error.__cause__
    constraint = getattr(getattr(cause, "diag", None), "constraint_name", None)
    return (
        isinstance(error, PageUrlConflict)
        or constraint == "unique_site_language_path"
        or (connection.vendor == "mysql" and error.args and error.args[0] == 1062
            and "unique_site_language_path" in str(error))
        or (connection.vendor == "sqlite" and str(error) == (
            "UNIQUE constraint failed: cms_pageurl.site_id, cms_pageurl.language, cms_pageurl.path"
        ))
    )


@contextmanager
def page_url_errors(data):
    """Translate only known URL conflicts, after rolling back the failed write."""
    try:
        with transaction.atomic():
            yield
    except IntegrityError as error:
        if not _is_url_conflict(error):
            raise
        field = "overwrite_url" if data.get("overwrite_url") else "slug"
        raise ValidationError({field: _("A page with this URL already exists.")}) from error


def page_write(*targets, refresh=True, translate_errors=True):
    """Lock the sites of named Site/Page/PageContent arguments until commit.

    A site row exists even for the first page, unlike a page/tree lock. Locking
    all affected sites in primary-key order also covers cross-site copies.
    SQLite has no row locks: a no-op UPDATE obtains its database write lock
    before any page reads instead. Callers must acquire these locks before
    taking tree/page locks and use the default database, like page services.

    Refresh inputs only after locking: their paths, related objects and custom
    caches may have been loaded before another operation committed. The legacy
    advanced-settings entry point opts out to preserve its pending edits.
    """
    def decorate(func):
        sig = signature(func)

        @wraps(func)
        def wrapped(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            objects = [bound.arguments.get(name) for name in targets]
            site_ids = {
                obj.pk if isinstance(obj, Site) else obj.site_id if hasattr(obj, "site_id") else obj.page.site_id
                for obj in objects if obj is not None
            }
            if not site_ids:
                site_ids = {Site.objects.get_current().pk}
            with transaction.atomic():
                sites = Site.objects.filter(pk__in=site_ids).order_by("pk")
                if connection.vendor == "sqlite":
                    sites.update(domain=F("domain"))
                else:
                    list(sites.select_for_update())
                if refresh:
                    for obj in objects:
                        if obj is not None and obj.pk and not isinstance(obj, Site):
                            obj.refresh_from_db()
                            if hasattr(obj, "_clear_internal_cache"):
                                obj._clear_internal_cache()
                                obj.__dict__.pop("_ancestors", None)
                                obj.__dict__.pop("_descendants", None)
                if translate_errors:
                    data = bound.arguments.get("data") or bound.arguments.get("content_data") or {}
                    with page_url_errors(data):
                        return func(*args, **kwargs)
                return func(*args, **kwargs)

        return wrapped
    return decorate

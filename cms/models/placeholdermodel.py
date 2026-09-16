"""Moved to :mod:`cms.core.models.placeholder`.

Kept importable because the ecosystem imports from this path, and because
``cms.models`` star-imports it (see :mod:`cms.compat`).
"""

from cms.compat import moved

__getattr__, __dir__, __all__ = moved(
    __name__,
    {
        "ContentType": "cms.core.models.placeholder.ContentType",
        "EXPIRE_NOW": "cms.core.models.placeholder.EXPIRE_NOW",
        "GenericForeignKey": "cms.core.models.placeholder.GenericForeignKey",
        "Iterable": "cms.core.models.placeholder.Iterable",
        "LanguageError": "cms.core.models.placeholder.LanguageError",
        "MAX_EXPIRATION_TTL": "cms.core.models.placeholder.MAX_EXPIRATION_TTL",
        "Placeholder": "cms.core.models.placeholder.Placeholder",
        "PlaceholderManager": "cms.core.models.placeholder.PlaceholderManager",
        "TYPE_CHECKING": "cms.core.models.placeholder.TYPE_CHECKING",
        "clear_placeholder_cache": "cms.core.models.placeholder.clear_placeholder_cache",
        "connection": "cms.core.models.placeholder.connection",
        "datetime": "cms.core.models.placeholder.datetime",
        "force_str": "cms.core.models.placeholder.force_str",
        "get_cms_setting": "cms.core.models.placeholder.get_cms_setting",
        "get_language_from_request": "cms.core.models.placeholder.get_language_from_request",
        "get_language_object": "cms.core.models.placeholder.get_language_object",
        "get_site_id": "cms.core.models.placeholder.get_site_id",
        "lazy": "cms.core.models.placeholder.lazy",
        "models": "cms.core.models.placeholder.models",
        "permissions": "cms.core.models.placeholder.permissions",
        "placeholder_cache_cleared": "cms.core.models.placeholder.placeholder_cache_cleared",
        "resolve": "cms.core.models.placeholder.resolve",
        "timedelta": "cms.core.models.placeholder.timedelta",
        "title": "cms.core.models.placeholder.title",
        "transaction": "cms.core.models.placeholder.transaction",
        "warnings": "cms.core.models.placeholder.warnings",
    },
    since="6.0",
    fallback="cms.core.models.placeholder",
)

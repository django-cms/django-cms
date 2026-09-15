"""Signals containers use to notify each other.

A container announces what happened inside it; other containers decide what
that means for them. Nothing here imports a container, so a container can send
or receive without taking a dependency on its peers -- which is the point: the
two signals below exist because ``cms.models.pagemodel`` used to call
``menus.menu_pool`` directly, and ``cms.models.placeholdermodel`` used to call
the *page* cache directly. Both were import cycles through the model layer.

Receivers for these live in :mod:`cms.signals.cache`.
"""

from django.dispatch import Signal

#: A placeholder's rendered content cache was cleared.
#:
#: Sent by ``Placeholder.clear_cache``. Anything whose cache embeds rendered
#: placeholder content -- the page cache, for one -- is now stale.
#:
#: :param sender: the :class:`~cms.models.placeholdermodel.Placeholder` class
#: :param placeholder: the placeholder whose cache was cleared
#: :param language: language code the cache was cleared for
#: :param site_id: site the placeholder belongs to, or ``None``
placeholder_cache_cleared = Signal()

#: A page's derived caches were invalidated.
#:
#: Sent by ``Page.clear_cache``. ``menu`` and ``placeholder`` carry the
#: caller's intent rather than describing work already done, so a receiver can
#: tell a routine content change from a structural one that also invalidates
#: navigation.
#:
#: :param sender: the :class:`~cms.models.pagemodel.Page` class
#: :param page: the page whose caches were invalidated
#: :param language: language code, or ``None`` for all languages
#: :param menu: ``True`` if navigation caches for the page's site are stale
#: :param placeholder: ``True`` if the page's placeholder caches were cleared
page_caches_invalidated = Signal()

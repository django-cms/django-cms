######
Titles
######

..  class:: cms.models.Title

    Titles support pages by providing a storage mechanism, amongst other things, for language-specific
    properties of :class:`cms.models.Page`, such as its title, slug, meta description and so on.

    Each ``Title`` has a foreign key to :class:`cms.models.Page`; each :class:`cms.models.Page` may have several
    ``Titles``.

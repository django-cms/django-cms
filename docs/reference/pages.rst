######
Models
######

..  class:: cms.models.Page

    A ``Page`` is the basic unit of site structure in django CMS. The CMS uses a hierachical page model: each page
    stands in relation to other pages as parent, child or sibling.

    A ``Page`` also has language-specific properties - for example, it will have a title and a slugfor each language it
    exists in. These properties are managed by the :class:`cms.models.Title` model.

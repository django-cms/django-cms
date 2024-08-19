Search and django CMS
=====================

.. seealso::

    - :ref:`Version States <version_states>`
    - `djangocms-versioning <https://github.com/django-cms/djangocms-versioning>`_
    - `django-haystack <https://github.com/django-haystack/django-haystack>`_

If you already have a background in django CMS and are coming from the 3.x days, you may 
be familiar with the package ``aldryn-search`` which was the recommended way for setting up
search inside your django CMS project. However, with the deprecation of it and the new
versioning primitives in django CMS 4.x being incompatible with it, you may wonder where to
go from here. 

To keep it simple, you can install an external package that handles implementing the search 
index for you. There are multiple options, such as

* `djangocms-aldryn-search <https://github.com/CZ-NIC/djangocms-aldryn-search>`_
* `djangocms-haystack <https://github.com/Lfd4/djangocms-haystack>`_
* ... and others

The idea is that we implement the search index just as we would for normal Django models,
e.g. use an external library to handle the indexing (``django-haystack`` in the above examples)
and just implement the logic that builds the querysets and filters the languages depending on
what index is currently active. ``django-haystack`` exposes many helpful utilities for 
interacting with the indexes and return the appropriate results for indexing.

To get an idea on how this works, feel free to look at the code of the above projects.
A very simple index could look something like this:

..  code-block:: python
    :emphasize-lines: 3

    from cms.models import PageContent
    from django.db import models
    from haystack import indexes


    class PageContentIndex(indexes.SearchIndex, indexes.Indexable):
        text = indexes.CharField(document=True, use_template=False)
        title = indexes.CharField(indexed=False, stored=True)
        url = indexes.CharField(indexed=False, stored=True)

        def get_model(self):
            return PageContent

        def index_queryset(self, using=None) -> models.QuerySet:
            return self.get_model().objects.filter(language=using)

        def prepare(self, instance: PageContent) -> dict:
          self.prepared_data = super().prepare(instance)
          self.prepared_data["url"] = instance.page.get_absolute_url()
          self.prepared_data["title"] = instance.title
          self.prepared_data["text"] = (
            self.prepared_data["title"] + (instance.meta_description or "")
          )
          return self.prepared_data

.. hint::
  Your index should be placed inside a ``search_indexes.py`` in one of your
  ``INSTALLED_APPS``!

The above snippet uses the standard ``text`` field that is recommended by 
``django-haystack`` to store all the indexable content. There is also a 
separate field for the title because you may want to display it as a heading
in your search result, and a field for the URL so you can link to the pages.

The indexed content here is *not* using a template (which is one of the options
to compose fields into an indexable field) but rather concatenates it manually
using the ``prepare`` method which gets called by ``django-haystack`` to prepare data
before the indexing starts.

As you can see in the ``index_queryset`` method, we only return those ``PageContent``
instances that are ``published`` and have a language matching the currently used
Haystack connection key.

The ``PageContent`` then get passed into the ``prepare`` method one by one, so we can
use the ``instance.page`` attribute to get the page meta description and use it as 
indexable text as well as the title of the current ``PageContent`` version.

Finally, you need to set your ``HAYSTACK_CONNECTIONS`` to contain a default key as 
well as **any language that you want to be indexed** as additional keys.
You could also use different backends for your languages as well, this is up to you
and how you want to configure your haystack installation. 
An example could look somewhat like this:

..  code-block:: python
    :emphasize-lines: 3

    ...

    HAYSTACK_CONNECTIONS = {
      'default': {
            "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
            "PATH": os.path.join(ROOT_DIR, "search_index", "whoosh_index_default"),
      },
      "en": {
          "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
          "PATH": os.path.join(ROOT_DIR, "search_index", "whoosh_index_en"),
      },
      "de": {
          "ENGINE": "haystack.backends.whoosh_backend.WhooshEngine",
          "PATH": os.path.join(ROOT_DIR, "search_index", "whoosh_index_de"),
      }
    }

    ...

.. hint::
  This should be configured in your projects ``settings.py``!

Now run ``python manage.py rebuild_index`` to start building your index. Depending on
what backend you chose you should now see your index at the configured location.

You can inspect your index using a ``SearchQuerySet``:

..  code-block:: python
    :emphasize-lines: 3

    from haystack.query import SearchQuerySet

    qs = SearchQuerySet(using="<your haystack connection alias / language key>")
    for result in qs.all():
      print(result.text)

Now it's up to you to add custom indexes to your own models, build views for your 
``SearchQuerySet`` to implement a search form and much more.

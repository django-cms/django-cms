from django.conf import settings
from django.utils.translation import string_concat, ugettext_lazy

from haystack import indexes, site

from cms.models.managers import PageManager
from cms.models.pagemodel import Page

def page_index_factory(lang, lang_name):
    if isinstance(lang_name, basestring):
        lang_name = ugettext_lazy(lang_name)

    def get_absolute_url(self):
        return '/%s%s' % (lang, Page.get_absolute_url(self))

    class Meta:
        proxy = True
        app_label = 'cms'
        verbose_name = string_concat(Page._meta.verbose_name, ' (', lang_name, ')')
        verbose_name_plural = string_concat(Page._meta.verbose_name_plural, ' (', lang_name, ')')
        
    attrs = {'__module__': Page.__module__, 
             'Meta': Meta,
             'objects': PageManager(),
             'get_absolute_url': get_absolute_url}
    
    _PageProxy = type("Page%s" % lang.title() , (Page,), attrs)
    
    _PageProxy._meta.parent_attr = 'parent'
    _PageProxy._meta.left_attr = 'lft'
    _PageProxy._meta.right_attr = 'rght'
    _PageProxy._meta.tree_id_attr = 'tree_id'
    
    class _PageIndex(indexes.SearchIndex):
        language = lang
        
        text = indexes.CharField(document=True, use_template=False)
        pub_date = indexes.DateTimeField(model_attr='publication_date')
        login_required = indexes.BooleanField(model_attr='login_required')
        url = indexes.CharField(stored=True, indexed=False, model_attr='get_absolute_url')
        title = indexes.CharField(stored=True, indexed=False, model_attr='get_title')
        
        def prepare(self, obj):
            self.prepared_data = super(_PageIndex, self).prepare(obj)
            plugins = obj.cmsplugin_set.filter(language=lang)
            text = ''
            for plugin in plugins:
                instance, _ = plugin.get_plugin_instance()
                if hasattr(instance, 'search_fields'):
                    text += ''.join(getattr(instance, field) for field in instance.search_fields)
            self.prepared_data['text'] = text
            return self.prepared_data
        
        def get_queryset(self):
            return _PageProxy.objects.published().filter(title_set__language=lang, publisher_is_draft=False).distinct()

    return _PageProxy, _PageIndex

for lang_tuple in settings.LANGUAGES:
    lang, lang_name = lang_tuple
    site.register(*page_index_factory(lang, lang_name))
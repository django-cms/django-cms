from django.core.exceptions import MultipleObjectsReturned

def get_page_from_placeholder_if_exists(placeholder):
    from cms.models.pagemodel import Page
    try:
        return Page.objects.get(placeholders=placeholder)
    except (Page.DoesNotExist, MultipleObjectsReturned,):
        return None
    
class PlaceholderNoAction(object):
    can_copy = False
    
    def copy(self, **kwargs):
        return False
    
    def get_copy_languages(self, **kwargs):
        return []
    
    
class MLNGPlaceholderActions(PlaceholderNoAction):
    can_copy = True

    def copy(self, target_placeholder, source_language, fieldname, model, target_language, **kwargs):
        trgt = model.objects.get(**{fieldname: target_placeholder})
        src = model.objects.get(master=trgt.master, language_code=source_language)

        source_placeholder = getattr(src, fieldname, None)
        plugins = source_placeholder.get_plugins_list()
        if source_placeholder:
            target_placeholder = source_placeholder
            target_placeholder.pk = None
            target_placeholder.save()
        ptree = []
        new_plugins = []
        for p in plugins:
            new_plugins.append(p.copy_plugin(target_placeholder, target_language, ptree))

        setattr(trgt, fieldname, target_placeholder)
        trgt.save()
        return new_plugins
    
    def get_copy_languages(self, placeholder, model, fieldname, **kwargs):
        from multilingual.languages import get_language_name
        src = model.objects.get(**{fieldname: placeholder})
        language_codes = model.objects.exclude(pk=src.pk).filter(master=src.master).exclude(**{'%s__cmsplugin' % fieldname: None}).values_list('language_code', flat=True)
        return [(lc, get_language_name(lc)) for lc in language_codes]
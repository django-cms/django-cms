from cms.models.pagemodel import Page

def get_page_from_placeholder_if_exists(placeholder):
    try:
        return Page.objects.get(placeholders=placeholder)
    except Page.DoesNotExist:
        return None
    
def mlng_placeholder_copy(placeholder, plugins, target_language, fieldname, model, **kwargs):
        src = model.objects.get(**{fieldname: placeholder})
        trgt, created = model.objects.get_or_create(master=src.master, language_code=target_language)

        old_placeholder = getattr(trgt, fieldname, None)
        if old_placeholder:
            placeholder = old_placeholder
        else:
            placeholder.pk = None
            placeholder.save()
        ptree = []
        for p in plugins:
            p.copy_plugin(placeholder, language, ptree)

        setattr(trgt, self.field, placeholder)
        trgt.save()
        return True
    
def mlng_placeholder_get_copy_langauges(placeholder, model, fieldname):
    src = model.objects.get(**{fieldname: placeholder})
    return model.objects.exclude(pk=src.pk).filter(master=src.master).values_list('language_code', flat=True)
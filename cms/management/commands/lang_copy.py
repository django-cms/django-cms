from copy import deepcopy

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from cms.models.pluginmodel import CMSPlugin

class Command(BaseCommand):
    args = '<language_code language_code>'
    help = 'dupplicate the cms content from one lang to another'

    def handle(self, *args, **kwargs):
        from_lang = args[0]
        to_lang = args[1]
        #test both langs
        try:
            assert len(args) == 2
            assert from_lang != to_lang
        except AssertionError:
            print 'available LANGUAGES :'+str(settings.LANGUAGES)
            raise CommandError("Error: bad arguments -- Usage: manage.py lang_copy en de")

        try:         
            assert list(k for k,v in settings.LANGUAGES if k == from_lang)
            assert list(k for k,v in settings.LANGUAGES if k == to_lang)
        except AssertionError:
            raise CommandError("Both languages have to be present in settings.LANGUAGES")

        for plugin in CMSPlugin.objects.filter(language=from_lang):
            if not CMSPlugin.objects.filter(language=to_lang, placeholder=plugin.placeholder, position=plugin.position).exists():
                plugin.copy_plugin(plugin.placeholder, to_lang, [])
        print 'DONE'

from copy import deepcopy
from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from cms.models.pluginmodel import CMSPlugin
from cms.models.titlemodels import Title


class LangCopyCommand(BaseCommand):
    args = '<language_from language_to>'
    help = 'duplicate the cms content from one lang to another (to boot a new lang)'

    option_list = BaseCommand.option_list + (
        make_option('--skipattrs', action='store_true', dest='skipattrs', default=False,
        help='Tells django-cms to NOT copy page attributes (like title, slug, id, plugin app, etc..). '),
    )

    def handle(self, *args, **kwargs):
        verbosity = kwargs.get('verbosity', 1)
        skip_attributes = kwargs.get('skipattrs', False)
        
        #test both langs
        try:
            assert len(args) == 2

            from_lang = args[0]
            to_lang = args[1]
            
            assert from_lang != to_lang
        except AssertionError:
            raise CommandError("Error: bad arguments -- Usage: manage.py cms copy-lang <lang_from> <lang_to>")
        
        try:
            assert from_lang in settings.LANGUAGES
            assert to_lang in settings.LANGUAGES
        except AssertionError:
            raise CommandError("Both languages have to be present in settings.LANGUAGES and settings.CMS_LANGUAGES")

        for plugin in CMSPlugin.objects.filter(language=from_lang):
            #copying content of the page
            if not CMSPlugin.objects.filter(language=to_lang, placeholder=plugin.placeholder, position=plugin.position).exists():
                if verbosity == "2":
                    print 'copying plugin from '+str(plugin)
                plugin.copy_plugin(plugin.placeholder, to_lang, [])

        if not skip_attributes:
            #copying attributes of the page
            for title in Title.objects.filter(language=from_lang):
                if not Title.objects.filter(page=title.page, language=to_lang).exists():
                    if verbosity == "2":
                        print 'copying title from '+str(title)
                    title.id = None
                    title.language = to_lang
                    title.save()
        elif verbosity == '2':
            print 'skipping attributes'

        if verbosity == '2':
            print 'DONE'

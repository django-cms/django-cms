# -*- coding: utf-8 -*-
from django.conf import settings

from django.core.management.base import BaseCommand, CommandError

from cms.api import copy_plugins_to_language
from cms.models import Page, StaticPlaceholder, EmptyTitle
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.i18n import get_language_list


class CopyLangCommand(BaseCommand):
    args = '<language_from language_to>'
    help = u'duplicate the cms content from one lang to another (to boot a new lang) using draft pages'

    def handle(self, *args, **kwargs):
        verbose = 'verbose' in args
        only_empty = 'force-copy' not in args
        site = [arg.split("=")[1] for arg in args if arg.startswith("site")]
        if site:
            site = site.pop()
        else:
            site = settings.SITE_ID

        #test both langs
        try:
            assert len(args) >= 2

            from_lang = args[0]
            to_lang = args[1]

            assert from_lang != to_lang
        except AssertionError:
            raise CommandError("Error: bad arguments -- Usage: manage.py cms copy-lang <lang_from> <lang_to>")

        try:
            assert from_lang in get_language_list(site)
            assert to_lang in get_language_list(site)
        except AssertionError:
            raise CommandError("Both languages have to be present in settings.LANGUAGES and settings.CMS_LANGUAGES")

        for page in Page.objects.on_site(site).drafts():
            # copy title
            if from_lang in page.get_languages():

                title = page.get_title_obj(to_lang, fallback=False)
                if isinstance(title, EmptyTitle):
                    title = page.get_title_obj(from_lang)
                    if verbose:
                        self.stdout.write('copying title %s from language %s\n' % (title.title, from_lang))
                    title.id = None
                    title.publisher_public_id = None
                    title.publisher_state = 0
                    title.language = to_lang
                    title.save()
                # copy plugins using API
                if verbose:
                    self.stdout.write('copying plugins for %s from %s\n' % (page.get_page_title(from_lang), from_lang))
                copy_plugins_to_language(page, from_lang, to_lang, only_empty)
            else:
                if verbose:
                    self.stdout.write('Skipping page %s, language %s not defined\n' % (page, from_lang))

        for static_placeholder in StaticPlaceholder.objects.all():
            plugin_list = []
            for plugin in static_placeholder.draft.get_plugins():
                if plugin.language == from_lang:
                    plugin_list.append(plugin)

            if plugin_list:
                if verbose:
                    self.stdout.write("copying plugins from static_placeholder '%s' in '%s' to '%s'\n" % (static_placeholder.name, from_lang,
                                                                                             to_lang))
                copy_plugins_to(plugin_list, static_placeholder.draft, to_lang)

        self.stdout.write(u"all done")

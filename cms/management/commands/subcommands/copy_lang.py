# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.core.management.base import CommandError

from cms.api import copy_plugins_to_language
from cms.models import Page, StaticPlaceholder, EmptyTitle
from cms.utils.copy_plugins import copy_plugins_to
from cms.utils.i18n import get_language_list

from .base import SubcommandsCommand


class CopyLangCommand(SubcommandsCommand):
    help_string = ('duplicate the cms content from one lang to another (to boot a new lang) '
                   'using draft pages')
    command_name = 'copy-lang'

    def add_arguments(self, parser):
        parser.add_argument('--from-lang', action='store', dest='from_lang', required=True,
                            help='Language to copy the content from.')
        parser.add_argument('--to-lang', action='store', dest='to_lang', required=True,
                            help='Language to copy the content to.')
        parser.add_argument('--site', action='store', dest='site',
                            help='Site to work on.')
        parser.add_argument('--force', action='store_false', dest='only_empty', default=True,
                            help='If set content is copied even if destination language already '
                                 'has content.')

    def handle(self, *args, **options):
        verbose = options.get('verbosity') > 1
        only_empty = options.get('only_empty')
        from_lang = options.get('from_lang')
        to_lang = options.get('to_lang')
        try:
            site = int(options.get('site', None))
        except Exception:
            site = settings.SITE_ID

        try:
            assert from_lang in get_language_list(site)
            assert to_lang in get_language_list(site)
        except AssertionError:
            raise CommandError('Both languages have to be present in settings.LANGUAGES and settings.CMS_LANGUAGES')

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
                    self.stdout.write('Skipping page %s, language %s not defined\n' % (page.get_page_title(page.get_languages()[0]), from_lang))

        for static_placeholder in StaticPlaceholder.objects.all():
            plugin_list = []
            for plugin in static_placeholder.draft.get_plugins():
                if plugin.language == from_lang:
                    plugin_list.append(plugin)

            if plugin_list:
                if verbose:
                    self.stdout.write(
                        'copying plugins from static_placeholder "%s" in "%s" to "%s"\n' % (
                            static_placeholder.name, from_lang, to_lang)
                    )
                copy_plugins_to(plugin_list, static_placeholder.draft, to_lang)

        self.stdout.write('all done')

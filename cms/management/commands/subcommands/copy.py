# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import CommandError
from django.db import transaction

from cms.api import copy_plugins_to_language
from cms.management.commands.subcommands.base import SubcommandsCommand
from cms.models import Page, StaticPlaceholder, EmptyTitle
from cms.utils import get_language_list
from cms.utils.copy_plugins import copy_plugins_to


class CopyLangCommand(SubcommandsCommand):
    help_string = ('Duplicate the cms content from one lang to another (to boot a new lang) '
                   'using draft pages')
    command_name = 'lang'
    label = 'plugin name (eg SamplePlugin)'

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
        parser.add_argument('--skip-content', action='store_false', dest='copy_content',
                            default=True, help='If set content is not copied, and the command '
                                               'will only create titles in the given language.')

    def handle(self, *args, **options):
        verbose = options.get('verbosity') > 1
        only_empty = options.get('only_empty')
        copy_content = options.get('copy_content')
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
                if copy_content:
                    # copy plugins using API
                    if verbose:
                        self.stdout.write('copying plugins for %s from %s\n' % (page.get_page_title(from_lang), from_lang))
                    copy_plugins_to_language(page, from_lang, to_lang, only_empty)
            else:
                if verbose:
                    self.stdout.write('Skipping page %s, language %s not defined\n' % (page.get_page_title(page.get_languages()[0]), from_lang))

        if copy_content:
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


class CopySiteCommand(SubcommandsCommand):
    help_string = 'Duplicate the CMS pagetree from a specific SITE_ID.'
    command_name = 'site'

    def add_arguments(self, parser):
        parser.add_argument('--from-site', action='store', dest='from_site', required=True,
                            help='Language to copy the content from.')
        parser.add_argument('--to-site', action='store', dest='to_site', required=True,
                            help='Language to copy the content to.')

    def handle(self, *args, **options):
        try:
            from_site = int(options.get('from_site', None))
        except Exception:
            from_site = settings.SITE_ID
        try:
            to_site = int(options.get('to_site', None))
        except Exception:
            to_site = settings.SITE_ID
        try:
            assert from_site != to_site
        except AssertionError:
            raise CommandError('Sites must be different')

        from_site = self.get_site(from_site)
        to_site = self.get_site(to_site)

        pages = Page.objects.drafts().filter(site=from_site, depth=1)

        with transaction.atomic():
            for page in pages:
                page.copy_page(None, to_site)
            self.stdout.write('Copied CMS Tree from SITE_ID {0} successfully to SITE_ID {1}.\n'.format(from_site.pk, to_site.pk))

    def get_site(self, site_id):
        if site_id:
            try:
                return Site.objects.get(pk=site_id)
            except (ValueError, Site.DoesNotExist):
                raise CommandError('There is no site with given site id.')
        else:
            return None


class CopyCommand(SubcommandsCommand):
    help_string = 'Copy content from one language or site to another'
    command_name = 'copy'
    missing_args_message = 'foo bar'
    subcommands = {
        'lang': CopyLangCommand,
        'site': CopySiteCommand
    }

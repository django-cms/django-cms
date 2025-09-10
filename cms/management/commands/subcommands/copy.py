from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import CommandError
from django.db import transaction

from cms.api import copy_plugins_to_language
from cms.management.commands.subcommands.base import SubcommandsCommand
from cms.models import EmptyPageContent, Page, PageContent, PageUrl, StaticPlaceholder
from cms.utils import get_language_list
from cms.utils.page import get_available_slug
from cms.utils.plugins import copy_plugins_to_placeholder

User = get_user_model()


def get_user(options):
    if options["userid"] and options["username"]:  # pragma: no cover
        raise CommandError("Only either one of the options '--userid' or '--username' may be given")
    if options["userid"]:
        try:
            return User.objects.get(pk=options["userid"])
        except User.DoesNotExist:
            raise CommandError(f"No user with id {options['userid']} found")
    if options["username"]:  # pragma: no cover
        try:
            return User.objects.get(username=options["username"])
        except User.DoesNotExist:
            raise CommandError(f"No user with name {options['username']} found")
    return None  # pragma: no cover


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
        parser.add_argument("--username", type=str, dest='username', default="",
                            help="Username of user needed create new content objects")
        parser.add_argument("--userid", type=int, help="User id of user needed create new content objects")

    def handle(self, *args, **options):
        verbose = options.get('verbosity') > 1
        only_empty = options.get('only_empty')
        copy_content = options.get('copy_content')
        from_lang = options.get('from_lang')
        to_lang = options.get('to_lang')
        user = get_user(options)

        try:
            site = int(options.get('site', None))
        except Exception:
            site = settings.SITE_ID

        try:
            assert from_lang in get_language_list(site)
            assert to_lang in get_language_list(site)
        except AssertionError:
            raise CommandError('Both languages have to be present in settings.LANGUAGES and settings.CMS_LANGUAGES')

        # obey node path (tree order) to make sure parent records are created before children (for slug generation)
        for page in Page.objects.on_site(site).order_by('path'):
            # copy title
            if from_lang in page.get_languages():

                title = page.get_content_obj(to_lang, fallback=False)
                if isinstance(title, EmptyPageContent):
                    title = page.get_content_obj(from_lang)
                    if verbose:
                        self.stdout.write(f'copying page content {title.title} from language {from_lang}\n')
                    if not user:
                        raise CommandError('Specify either --userid or --username')
                    from django.forms import model_to_dict
                    new_title = model_to_dict(title)
                    new_title.pop("id", None)  # No PK
                    new_title["language"] = to_lang
                    new_title["page"] = page
                    PageContent.objects.with_user(user).create(**new_title)

                    if to_lang not in page.get_languages():
                        page.update_languages(page.get_languages() + [to_lang])

                    # copy PageUrls - inspired from pagemodels.Page.copy() - possibly refactorable
                    page_url = page.urls.get(language=from_lang)
                    parent_page = page.parent

                    new_url = model_to_dict(page_url)
                    new_url.pop("id", None)  # No PK
                    new_url["page"] = page
                    new_url["language"] = to_lang

                    if parent_page:
                        base = parent_page.get_path(to_lang)
                        path = '%s/%s' % (base, page_url.slug) if base else page_url.slug
                    else:
                        base = ''
                        path = page_url.slug

                    new_url["slug"] = get_available_slug(site, path, to_lang)
                    new_url["path"] = '%s/%s' % (base, new_url["slug"]) if base else new_url["slug"]
                    PageUrl.objects.with_user(user).create(**new_url)

                if copy_content:
                    # copy plugins using API
                    if verbose:
                        self.stdout.write(
                            f'copying plugins for {page.get_page_title(from_lang)} from {from_lang}\n'
                        )
                    copy_plugins_to_language(page, from_lang, to_lang, only_empty)
            else:
                if verbose:
                    self.stdout.write(
                        f'Skipping page {page.get_page_title(page.get_languages()[0])}, language {from_lang} not defined\n'
                    )

        if copy_content:
            for static_placeholder in StaticPlaceholder.objects.all():
                plugin_list = []
                for plugin in static_placeholder.draft.get_plugins():
                    if plugin.language == from_lang:
                        plugin_list.append(plugin)

                if plugin_list:
                    if verbose:
                        self.stdout.write(
                            f'copying plugins from static_placeholder "{static_placeholder.name}" in "{from_lang}" to "{to_lang}"\n'
                        )
                    copy_plugins_to_placeholder(
                        plugins=plugin_list,
                        placeholder=static_placeholder.draft,
                        language=to_lang,
                    )

        self.stdout.write('all done')


class CopySiteCommand(SubcommandsCommand):
    help_string = 'Duplicate the CMS pagetree from a specific SITE_ID.'
    command_name = 'site'

    def add_arguments(self, parser):
        parser.add_argument('--from-site', action='store', dest='from_site', required=True,
                            help='Language to copy the content from.')
        parser.add_argument('--to-site', action='store', dest='to_site', required=True,
                            help='Language to copy the content to.')
        parser.add_argument("--username", type=str, dest='username', default="",
                            help="Username of user needed create new content objects")
        parser.add_argument("--userid", type=int, help="User id of user needed create new content objects")

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
        user = get_user(options)
        if not user:
            raise CommandError('Specify either --userid or --username')

        pages = (
            Page
            .objects
            .on_site(from_site)
            .filter(depth=1)
            .order_by('path')
        )

        with transaction.atomic():
            for page in pages:
                new_page = page.copy_with_descendants(
                    target_page=None,
                    target_site=to_site,
                    user=user,
                )

                if page.is_home:
                    new_page.set_as_homepage()
        self.stdout.write(
            f'Copied CMS Tree from SITE_ID {from_site.pk} successfully to SITE_ID {to_site.pk}.\n'
        )

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

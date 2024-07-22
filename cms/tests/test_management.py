import uuid
from io import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core import management
from django.core.management import CommandError
from django.db import models
from django.test.utils import override_settings
from djangocms_text_ckeditor.cms_plugins import TextPlugin

from cms.api import add_plugin, create_page, create_page_content
from cms.management.commands.subcommands.list import plugin_report
from cms.models import Page, StaticPlaceholder
from cms.models.placeholdermodel import Placeholder
from cms.models.pluginmodel import CMSPlugin
from cms.test_utils.fixtures.navextenders import NavextendersFixture
from cms.test_utils.project.sampleapp.cms_apps import SampleApp
from cms.test_utils.testcases import CMSTestCase
from cms.test_utils.util.context_managers import apphooks

APPHOOK = "SampleApp"
PLUGIN = "TextPlugin"

TEST_INSTALLED_APPS = [
    "django.contrib.auth",
    "cms",
    "menus",
    "sekizai",
    "treebeard",
] + settings.PLUGIN_APPS
if settings.AUTH_USER_MODEL == "emailuserapp.EmailUser":
    TEST_INSTALLED_APPS.append("cms.test_utils.project.emailuserapp")
if settings.AUTH_USER_MODEL == "customuserapp.User":
    TEST_INSTALLED_APPS.append("cms.test_utils.project.customuserapp")


class ManagementTestCase(CMSTestCase):
    @override_settings(INSTALLED_APPS=TEST_INSTALLED_APPS)
    def test_list_apphooks(self):
        with apphooks(SampleApp):
            out = StringIO()
            create_page('Hello Title', "nav_playground.html", "en", apphook=APPHOOK)
            self.assertEqual(Page.objects.filter(application_urls=APPHOOK).count(), 1)
            management.call_command(
                "cms",
                "list",
                "apphooks",
                interactive=False,
                stdout=out,
            )
            self.assertEqual(out.getvalue(), "SampleApp (active)\n")

    def test_uninstall_apphooks_without_apphook(self):
        with apphooks():
            out = StringIO()
            management.call_command(
                "cms",
                "uninstall",
                "apphooks",
                APPHOOK,
                interactive=False,
                stdout=out,
            )
            self.assertEqual(out.getvalue(), "no 'SampleApp' apphooks found\n")

    def test_fix_tree(self):
        create_page("home", "nav_playground.html", "en")
        page1 = create_page("page", "nav_playground.html", "en")
        page1.depth = 3
        page1.numchild = 4
        page1.path = "00100010"
        page1.save()
        out = StringIO()
        management.call_command('cms', 'fix-tree', interactive=False, stdout=out)
        self.assertEqual(out.getvalue(), 'fixing page tree\nall done\n')
        page1 = page1.reload()
        self.assertEqual(page1.path, "0002")
        self.assertEqual(page1.depth, 1)
        self.assertEqual(page1.numchild, 0)

    def test_fix_tree_regression_5641(self):
        # ref: https://github.com/divio/django-cms/issues/5641
        alpha = create_page("Alpha", "nav_playground.html", "en")
        beta = create_page("Beta", "nav_playground.html", "en")
        gamma = create_page("Gamma", "nav_playground.html", "en")
        delta = create_page("Delta", "nav_playground.html", "en")
        theta = create_page("Theta", "nav_playground.html", "en")

        beta.move_page(alpha, position='last-child')
        gamma.move_page(beta, position='last-child')
        delta.move_page(gamma, position='last-child')
        theta.move_page(delta, position='last-child')

        out = StringIO()
        management.call_command('cms', 'fix-tree', interactive=False, stdout=out)

        tree = [
            (alpha, '0001'),
            (beta, '00010001'),
            (gamma, '000100010001'),
            (delta, '0001000100010001'),
            (theta, '00010001000100010001'),
        ]

        for page, path in tree:
            self.assertEqual(page.path, path)

    @override_settings(INSTALLED_APPS=TEST_INSTALLED_APPS)
    def test_uninstall_apphooks_with_apphook(self):
        with apphooks(SampleApp):
            out = StringIO()
            create_page('Hello Title', "nav_playground.html", "en", apphook=APPHOOK)
            self.assertEqual(Page.objects.filter(application_urls=APPHOOK).count(), 1)
            management.call_command(
                "cms",
                "uninstall",
                "apphooks",
                APPHOOK,
                interactive=False,
                stdout=out,
            )
            self.assertEqual(out.getvalue(), "1 'SampleApp' apphooks uninstalled\n")
            self.assertEqual(Page.objects.filter(application_urls=APPHOOK).count(), 0)

    @override_settings(INSTALLED_APPS=TEST_INSTALLED_APPS)
    def test_list_plugins(self):
        out = StringIO()
        placeholder = Placeholder.objects.create(slot="test")
        add_plugin(placeholder, TextPlugin, "en", body="en body")
        add_plugin(placeholder, TextPlugin, "en", body="en body")
        link_plugin = add_plugin(placeholder, "LinkPlugin", "en",
                                 name="A Link", external_link="https://www.django-cms.org")
        self.assertEqual(
            CMSPlugin.objects.filter(plugin_type=PLUGIN).count(),
            2)
        self.assertEqual(
            CMSPlugin.objects.filter(plugin_type="LinkPlugin").count(),
            1)

        # create a CMSPlugin with an unsaved instance
        instanceless_plugin = CMSPlugin.objects.create(
            position=4,
            language="en",
            plugin_type="TextPlugin",
            placeholder=placeholder,
        )

        # create a bogus CMSPlugin to simulate one which used to exist but
        # is no longer installed
        bogus_plugin = CMSPlugin.objects.create(
            position=5,
            language="en",
            plugin_type="BogusPlugin",
            placeholder=placeholder,
        )

        management.call_command('cms', 'list', 'plugins', interactive=False, stdout=out)
        report = plugin_report()

        # there should be reports for three plugin types
        self.assertEqual(
            len(report),
            3)

        # check the bogus plugin
        bogus_plugins_report = report[0]
        self.assertEqual(
            bogus_plugins_report["model"],
            None)

        self.assertEqual(
            bogus_plugins_report["type"],
            'BogusPlugin')

        self.assertEqual(
            bogus_plugins_report["instances"][0],
            bogus_plugin)

        # check the link plugin
        link_plugins_report = report[1]
        self.assertEqual(
            link_plugins_report["model"],
            link_plugin.__class__)

        self.assertEqual(
            link_plugins_report["type"],
            'LinkPlugin')

        self.assertEqual(
            link_plugins_report["instances"][0].get_plugin_instance()[0],
            link_plugin)

        # check the text plugins
        text_plugins_report = report[2]
        self.assertEqual(
            text_plugins_report["model"],
            TextPlugin.model)

        self.assertEqual(
            text_plugins_report["type"],
            'TextPlugin')

        self.assertEqual(
            len(text_plugins_report["instances"]),
            3)

        self.assertEqual(
            text_plugins_report["instances"][2],
            instanceless_plugin)

        self.assertEqual(
            text_plugins_report["unsaved_instances"],
            [instanceless_plugin])

    @override_settings(INSTALLED_APPS=TEST_INSTALLED_APPS)
    def test_delete_orphaned_plugins(self):
        placeholder = Placeholder.objects.create(slot="test")
        add_plugin(placeholder, TextPlugin, "en", body="en body")
        add_plugin(placeholder, "LinkPlugin", "en",
                   name="A Link", external_link="https://www.django-cms.org")

        instanceless_plugin = CMSPlugin(
            language="en", plugin_type="TextPlugin")
        instanceless_plugin.save()

        # create a bogus CMSPlugin to simulate one which used to exist but
        # is no longer installed
        bogus_plugin = CMSPlugin(language="en", plugin_type="BogusPlugin", placeholder=placeholder)
        placeholder.add_plugin(bogus_plugin)
        add_plugin(placeholder, TextPlugin, "en", body="en body")

        report = plugin_report()

        # there should be reports for three plugin types
        self.assertEqual(
            len(report),
            3)

        # check the bogus plugin
        bogus_plugins_report = report[0]
        self.assertEqual(
            len(bogus_plugins_report["instances"]),
            1)

        # check the link plugin
        link_plugins_report = report[1]
        self.assertEqual(
            len(link_plugins_report["instances"]),
            1)

        # check the text plugins
        text_plugins_report = report[2]
        self.assertEqual(
            len(text_plugins_report["instances"]),
            3)

        self.assertEqual(
            len(text_plugins_report["unsaved_instances"]),
            1)

        out = StringIO()
        management.call_command('cms', 'delete-orphaned-plugins', interactive=False, stdout=out)
        report = plugin_report()

        # there should be reports for two plugin types (one should have been deleted)
        self.assertEqual(
            len(report),
            2)

        # check the link plugin
        link_plugins_report = report[0]
        self.assertEqual(
            len(link_plugins_report["instances"]),
            1)

        # check the text plugins
        text_plugins_report = report[1]
        self.assertEqual(
            len(text_plugins_report["instances"]),
            2)

        self.assertEqual(
            len(text_plugins_report["unsaved_instances"]),
            0)

        # No gaps in plugin tree
        max_positon = placeholder.cmsplugin_set.aggregate(models.Max('position'))['position__max']
        self.assertEqual(max_positon, 3)


    def test_uninstall_plugins_without_plugin(self):
        out = StringIO()
        management.call_command('cms', 'uninstall', 'plugins', PLUGIN, interactive=False, stdout=out)
        self.assertEqual(out.getvalue(), "no 'TextPlugin' plugins found\n")

    @override_settings(INSTALLED_APPS=TEST_INSTALLED_APPS)
    def test_uninstall_plugins_with_plugin(self):
        out = StringIO()
        placeholder = Placeholder.objects.create(slot="test")
        add_plugin(placeholder, TextPlugin, "en", body="en body")
        self.assertEqual(CMSPlugin.objects.filter(plugin_type=PLUGIN).count(), 1)
        management.call_command('cms', 'uninstall', 'plugins', PLUGIN, interactive=False, stdout=out)
        self.assertEqual(out.getvalue(), "1 'TextPlugin' plugins uninstalled\n")
        self.assertEqual(CMSPlugin.objects.filter(plugin_type=PLUGIN).count(), 0)


class PageFixtureManagementTestCase(NavextendersFixture, CMSTestCase):

    def _fill_page_body(self, page, lang):
        ph_en = page.get_placeholders(lang).get(slot="body")
        # add misc plugins
        mcol1 = add_plugin(ph_en, "MultiColumnPlugin", lang, position="first-child")
        add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol1)
        col2 = add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol1)
        mcol2 = add_plugin(ph_en, "MultiColumnPlugin", lang, position="first-child", target=col2)
        add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol2)
        col4 = add_plugin(ph_en, "ColumnPlugin", lang, position="first-child", target=mcol2)
        # add a *nested* link plugin
        add_plugin(ph_en, "LinkPlugin", lang, target=col4, name="A Link", external_link="https://www.django-cms.org")
        static_placeholder = StaticPlaceholder(code=str(uuid.uuid4()), site_id=1)
        static_placeholder.save()
        add_plugin(static_placeholder.draft, "TextPlugin", lang, body="example content")

    def setUp(self):
        pages = Page.objects.all()
        for page in pages:
            self._fill_page_body(page, "en")

    def test_copy_langs(self):
        """
        Various checks here:

         * plugins are exactly doubled, half per language with no orphaned plugin
         * the bottom-most plugins in the nesting chain maintain the same position and the same content
         * the top-most plugin are of the same type
        """
        site = 1
        number_start_plugins = CMSPlugin.objects.all().count()

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=en', '--to-lang=de', '--userid=%d' % self.get_superuser().id,
            interactive=False, stdout=out
        )
        pages = Page.objects.on_site(site)
        for page in pages:
            self.assertEqual({'en', 'de'}, set(page.get_languages()))
        # These asserts that no orphaned plugin exists
        self.assertEqual(CMSPlugin.objects.all().count(), number_start_plugins * 2)
        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), number_start_plugins)
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), number_start_plugins)

        root_page = Page.objects.get_home(site)
        root_plugins = CMSPlugin.objects.filter(placeholder=root_page.get_placeholders('en').get(slot="body"))

        first_plugin_en, _ = root_plugins.get(language='en', parent=None).get_plugin_instance()
        first_plugin_de, _ = root_plugins.get(language='de', parent=None).get_plugin_instance()

        self.assertEqual(first_plugin_en.plugin_type, first_plugin_de.plugin_type)

        link_en, _ = root_plugins.get(language='en', plugin_type='LinkPlugin').get_plugin_instance()
        link_de, _ = root_plugins.get(language='de', plugin_type='LinkPlugin').get_plugin_instance()

        self.assertEqual(link_en.external_link, link_de.external_link)
        self.assertEqual(link_en.position, link_de.position)

        stack_plugins = CMSPlugin.objects.filter(placeholder=StaticPlaceholder.objects.order_by('?')[0].draft)

        stack_text_en, _ = stack_plugins.get(language='en', plugin_type='TextPlugin').get_plugin_instance()
        stack_text_de, _ = stack_plugins.get(language='de', plugin_type='TextPlugin').get_plugin_instance()

        self.assertEqual(stack_text_en.plugin_type, stack_text_de.plugin_type)
        self.assertEqual(stack_text_en.body, stack_text_de.body)

    def test_copy_langs_no_content(self):
        """
        Various checks here:

         * page structure is copied
         * no plugin is copied
        """
        site = 1
        number_start_plugins = CMSPlugin.objects.all().count()

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=en', '--to-lang=de', '--skip-content',
            '--userid=%d' % self.get_superuser().id,
            interactive=False, stdout=out
        )
        pages = Page.objects.on_site(site)
        for page in pages:
            self.assertEqual({'en', 'de'}, set(page.get_languages()))
        # These asserts that no orphaned plugin exists
        self.assertEqual(CMSPlugin.objects.all().count(), number_start_plugins)
        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), number_start_plugins)
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), 0)

        root_page = Page.objects.get_home(site)
        root_plugins = CMSPlugin.objects.filter(
            placeholder=root_page.get_placeholders('en').get(slot="body"))

        first_plugin_en, _ = root_plugins.get(language='en', parent=None).get_plugin_instance()
        first_plugin_de = None
        with self.assertRaises(CMSPlugin.DoesNotExist):
            first_plugin_de, _ = root_plugins.get(language='de', parent=None).get_plugin_instance()

        self.assertIsNone(first_plugin_de)

        stack_plugins = CMSPlugin.objects.filter(
            placeholder=StaticPlaceholder.objects.order_by('?')[0].draft)

        stack_text_en, _ = stack_plugins.get(language='en',
                                             plugin_type='TextPlugin').get_plugin_instance()
        with self.assertRaises(CMSPlugin.DoesNotExist):
            stack_text_de, _ = stack_plugins.get(language='de',
                                                 plugin_type='TextPlugin').get_plugin_instance()

    def test_copy_sites(self):
        """
        Various checks here:

         * plugins are exactly doubled, half per site with no orphaned plugin
         * the bottom-most plugins in the nesting chain maintain the same position and the same content
         * the top-most plugin are of the same type
        """
        site_1_pk = 1
        site_1 = Site.objects.get(pk=site_1_pk)
        site_2 = Site.objects.create(name='site 2')
        site_2_pk = site_2.pk
        phs = []
        for page in Page.objects.on_site(site_1_pk):
            phs.extend(page.get_placeholders('en').values_list('pk', flat=True))
        number_start_plugins = CMSPlugin.objects.filter(placeholder__in=phs).count()

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'site', '--from-site=%s' % site_1_pk, '--to-site=%s' % site_2_pk,
            '--userid=%d' % self.get_superuser().id,
            stdout=out
        )

        pages_1 = list(Page.objects.on_site(site_1).order_by('path'))
        pages_2 = list(Page.objects.on_site(site_2).order_by('path'))
        for index, page in enumerate(pages_1):
            self.assertEqual(page.get_title('en'), pages_2[index].get_title('en'))
            self.assertEqual(page.depth, pages_2[index].depth)

        phs_1 = []
        phs_2 = []
        for page in Page.objects.on_site(site_1_pk):
            phs_1.extend(page.get_placeholders('en').values_list('pk', flat=True))
        for page in Page.objects.on_site(site_2_pk):
            phs_2.extend(page.get_placeholders('en').values_list('pk', flat=True))

        # These asserts that no orphaned plugin exists
        self.assertEqual(CMSPlugin.objects.filter(placeholder__in=phs_1).count(), number_start_plugins)
        self.assertEqual(CMSPlugin.objects.filter(placeholder__in=phs_2).count(), number_start_plugins)

        root_page_1 = Page.objects.get_home(site_1)
        root_page_2 = Page.objects.get_home(site_2)
        root_plugins_1 = CMSPlugin.objects.filter(placeholder=root_page_1.get_placeholders('en').get(slot="body"))
        root_plugins_2 = CMSPlugin.objects.filter(placeholder=root_page_2.get_placeholders('en').get(slot="body"))

        first_plugin_1, _ = root_plugins_1.get(language='en', parent=None).get_plugin_instance()
        first_plugin_2, _ = root_plugins_2.get(language='en', parent=None).get_plugin_instance()

        self.assertEqual(first_plugin_1.plugin_type, first_plugin_2.plugin_type)

        link_1, _ = root_plugins_1.get(language='en', plugin_type='LinkPlugin').get_plugin_instance()
        link_2, _ = root_plugins_2.get(language='en', plugin_type='LinkPlugin').get_plugin_instance()

        self.assertEqual(link_1.external_link, link_2.external_link)
        self.assertEqual(link_1.position, link_2.position)

    def test_copy_existing_title(self):
        """
        Even if a title already exists the copy is successful, the original
        title remains untouched
        """
        site = 1
        number_start_plugins = CMSPlugin.objects.all().count()

        # create an empty title language
        root_page = Page.objects.get_home(site)
        create_page_content("de", "root page de", root_page)

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=en', '--to-lang=de',
            '--userid=%d' % self.get_superuser().id,
            interactive=False, stdout=out
        )
        pages = Page.objects.on_site(site)
        for page in pages:
            self.assertEqual({'en', 'de'}, set(page.get_languages()))

        # Original PageContent untouched
        self.assertEqual("root page de", Page.objects.get_home(site).get_title("de"))

        # Plugins still copied
        self.assertEqual(CMSPlugin.objects.all().count(), number_start_plugins * 2)
        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), number_start_plugins)
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), number_start_plugins)

    def test_copy_filled_placeholder(self):
        """
        If an existing title in the target language has plugins in a placeholder
        that placeholder is skipped
        """
        site = 1
        number_start_plugins = CMSPlugin.objects.all().count()

        # create an empty title language
        root_page = Page.objects.get_home(site)
        create_page_content("de", "root page de", root_page)
        ph = root_page.get_placeholders('en').get(slot="body")
        add_plugin(ph, "TextPlugin", "de", body="Hello World")

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=en', '--to-lang=de',
            '--userid=%d' % self.get_superuser().id,
            interactive=False, stdout=out
        )

        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), number_start_plugins)
        # one placeholder (with 7 plugins) is skipped, so the difference must be 6
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), number_start_plugins - 6)

    def test_copy_filled_placeholder_force_copy(self):
        """
        If an existing title in the target language has plugins in a placeholder
        and the command is called with *force-copy*, the plugins are copied on
        top of the existing one
        """
        site = 1
        number_start_plugins = CMSPlugin.objects.all().count()

        # create an empty title language
        root_page = Page.objects.get_home(site)
        create_page_content("de", "root page de", root_page)
        ph = root_page.get_placeholders('en').get(slot="body")
        add_plugin(ph, "TextPlugin", "de", body="Hello World")

        root_plugins = CMSPlugin.objects.filter(placeholder=ph)
        text_de_orig, _ = root_plugins.get(language='de', plugin_type='TextPlugin').get_plugin_instance()

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=en', '--to-lang=de', '--force',
            '--userid=%d' % self.get_superuser().id,
            interactive=False,
            stdout=out
        )

        CMSPlugin.objects.filter(placeholder=root_page.get_placeholders('en').get(slot="body"))

        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), number_start_plugins)
        # we have an existing plugin in one placeholder, so we have one more
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), number_start_plugins + 1)

    def test_copy_from_non_existing_lang(self):
        """
        If an existing title in the target language has plugins in a placeholder
        and the command is called with *force-copy*, the plugins are copied on
        top of the existing one
        """
        site = 1
        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=de', '--to-lang=fr',
            '--userid=%d' % self.get_superuser().id,
            verbosity=3,
            interactive=False, stdout=out
        )
        text = out.getvalue()
        page_count = Page.objects.on_site(site).count() + 1
        for idx in range(1, page_count):
            self.assertTrue("Skipping page page%d, language de not defined" % idx in text)

    def test_copy_site_safe(self):
        """
        Check that copy of languages on one site does not interfere with other
        sites
        """
        site_other = 1
        site_active = 2
        origina_site1_langs = {}

        number_start_plugins = CMSPlugin.objects.all().count()
        site_obj = Site.objects.create(domain="sample2.com", name="sample2.com", pk=site_active)

        for page in Page.objects.on_site(1):
            origina_site1_langs[page.pk] = set(page.get_languages())

        p1 = create_page('page1', in_navigation=True, language='de', template='nav_playground.html', site=site_obj)
        create_page('page4', in_navigation=True, language='de', template='nav_playground.html', site=site_obj)
        create_page(
            'page2', in_navigation=True, parent=p1, language='de', template='nav_playground.html', site=site_obj
        )

        for page in Page.objects.on_site(site_active):
            self._fill_page_body(page, 'de')

        number_site2_plugins = CMSPlugin.objects.all().count() - number_start_plugins

        out = StringIO()
        management.call_command(
            'cms', 'copy', 'lang', '--from-lang=de', '--to-lang=fr', '--site=%s' % site_active,
            '--userid=%d' % self.get_superuser().id,
            interactive=False, stdout=out
        )

        for page in Page.objects.on_site(site_other):
            self.assertEqual(origina_site1_langs[page.pk], set(page.get_languages()))

        for page in Page.objects.on_site(site_active):
            self.assertEqual({'de', 'fr'}, set(page.get_languages()))

        # plugins for site 1
        self.assertEqual(CMSPlugin.objects.filter(language='en').count(), number_start_plugins)
        # plugins for site 2 de
        self.assertEqual(CMSPlugin.objects.filter(language='de').count(), number_site2_plugins)
        # plugins for site 2 fr
        self.assertEqual(CMSPlugin.objects.filter(language='fr').count(), number_site2_plugins)
        # global number of plugins
        self.assertEqual(CMSPlugin.objects.all().count(), number_start_plugins + number_site2_plugins * 2)

    def test_copy_bad_languages(self):
        out = StringIO()
        with self.assertRaises(CommandError) as command_error:
            management.call_command(
                'cms', 'copy', 'lang', '--from-lang=it', '--to-lang=fr',
                '--userid=%d' % self.get_superuser().id,
                interactive=False, stdout=out
            )

        self.assertEqual(
            str(command_error.exception),
            'Both languages have to be present in settings.LANGUAGES and settings.CMS_LANGUAGES'
        )

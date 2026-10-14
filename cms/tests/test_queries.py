from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.translation import override

from cms import operations
from cms.api import add_plugin, create_page, create_page_content
from cms.core import queries, services as plugin_services
from cms.core.models.placeholder import Placeholder
from cms.core.models.plugin import CMSPlugin
from cms.core.models.settings import UserSettings
from cms.models import Page, PageContent
from cms.pages import queries as page_queries
from cms.shared.checks import OperationBlocked, can
from cms.shared.lookups import lookup, lookup_many
from cms.shared.operations import OperationContext
from cms.test_utils.testcases import CMSTestCase


class ReadServicesTest(CMSTestCase):
    """The pilot subset of the read services (RFC 9n): editing reads (``admin=True``), scoped lookups, content tokens."""

    def setUp(self):
        super().setUp()
        self.admin = self.get_superuser()
        self.context = OperationContext(user=self.admin, language="en")
        self.page = create_page("Home", "nav_playground.html", "en")
        self.content = self.page.get_content_obj("en")
        self.placeholder = self.content.get_placeholders().get(slot="body")
        self.first = add_plugin(self.placeholder, "TextPlugin", "en", body="first")
        self.second = add_plugin(self.placeholder, "TextPlugin", "en", body="second")
        self.child = add_plugin(self.placeholder, "TextPlugin", "en", target=self.first, body="child")

    def context_for(self, user):
        return OperationContext(user=user, language="en")

    # -- sources and placeholders -------------------------------------------

    def test_source_and_its_placeholders(self):
        source = queries.get_source("cms.pagecontent", self.content.pk, self.context, admin=True)
        placeholders = queries.get_placeholders(source, self.context, admin=True)

        self.assertEqual(source, self.content)
        self.assertIn(self.placeholder, placeholders)
        self.assertEqual(list(placeholders), sorted(placeholders, key=lambda placeholder: placeholder.slot))

    def test_only_active_staff_read_drafts(self):
        # The page is public: its view permission alone would let anyone in.
        visitor = self._create_user("visitor")
        for user in (visitor, AnonymousUser(), None):
            with self.subTest(user=user):
                with self.assertRaises(PageContent.DoesNotExist):
                    queries.get_source("cms.pagecontent", self.content.pk, self.context_for(user), admin=True)
                with self.assertRaises(Placeholder.DoesNotExist):
                    queries.get_placeholder(self.placeholder.pk, self.context_for(user), admin=True)
                with self.assertRaises(CMSPlugin.DoesNotExist):
                    queries.get_plugin(self.first.pk, self.context_for(user), admin=True)

    def test_absent_and_hidden_look_the_same(self):
        visitor = self._create_user("visitor")
        with self.assertRaises(PageContent.DoesNotExist):
            queries.get_source("cms.pagecontent", 0, self.context, admin=True)
        with self.assertRaises(PageContent.DoesNotExist):
            queries.get_source("cms.pagecontent", self.content.pk, self.context_for(visitor), admin=True)

    def test_only_placeholder_owners_are_sources(self):
        with self.assertRaises(LookupError):
            queries.get_source("auth.user", self.admin.pk, self.context, admin=True)

    def test_a_clipboard_stays_private(self):
        # As the toolbar creates it: the clipboard's source is the user's settings.
        clipboard = Placeholder.objects.create(slot="clipboard")
        clipboard.source = UserSettings.objects.create(user=self.admin, language="en", clipboard=clipboard)
        clipboard.save()
        other = self._create_user("other", is_staff=True)

        self.assertEqual(queries.get_placeholder(clipboard.pk, self.context, admin=True), clipboard)
        with self.assertRaises(Placeholder.DoesNotExist):
            queries.get_placeholder(clipboard.pk, self.context_for(other), admin=True)

    # -- scoped lookups -----------------------------------------------------

    def test_lookups_are_registered_by_model_label(self):
        self.assertEqual(lookup("cms.placeholder", self.placeholder.pk, self.context, admin=True), self.placeholder)
        self.assertEqual(lookup("cms.PageContent", self.content.pk, self.context, admin=True), self.content)
        plugin = lookup("cms.cmsplugin", self.first.pk, self.context, admin=True)
        self.assertEqual(type(plugin).__name__, "Text")  # downcast
        self.assertEqual(
            [plugin.pk for plugin in lookup_many("cms.cmsplugin", [self.second.pk, self.first.pk], self.context, admin=True)],
            [self.second.pk, self.first.pk],
        )

    def test_unknown_label(self):
        with self.assertRaises(LookupError):
            lookup("cms.pageurl", self.page.pk, self.context)

    def test_declared_model_arguments_of_plugin_operations_have_lookups(self):
        # What an adapter needs to call the plugin operations.
        for operation_id in (operations.MOVE_PLUGIN, operations.ADD_PLUGIN, operations.DELETE_PLUGIN):
            for argument in operations.get_operation(operation_id).arguments:
                for label in argument.models:
                    with self.subTest(operation=operation_id, argument=argument.name):
                        pk = self.first.pk if "plugin" in label else self.placeholder.pk
                        self.assertTrue(lookup(label, pk, self.context, admin=True))

    # -- the plugin tree and its token --------------------------------------

    def test_plugin_tree(self):
        tree = queries.get_plugin_tree(self.placeholder, "en", self.context, admin=True)

        self.assertEqual([plugin.pk for plugin in tree.plugins], [self.first.pk, self.child.pk, self.second.pk])
        self.assertEqual([plugin.parent_id for plugin in tree.plugins], [None, self.first.pk, None])
        self.assertEqual(tree.plugins[0].body, "first")
        self.assertEqual(tree.token, queries.placeholder_token(self.placeholder, "en"))

    def test_plugin_tree_reads_the_plugins_once(self):
        # The token is computed from the rows the tree is built from: one query
        # for the plugin rows, one to downcast the text plugins, none for the token.
        placeholder = Placeholder.objects.get(pk=self.placeholder.pk)
        queries.may_read_source(self.admin, placeholder.source, admin=True)  # warm the permission caches
        with CaptureQueriesContext(connection) as captured:
            tree = queries.get_plugin_tree(placeholder, "en", self.context, admin=True)

        plugin_queries = [query for query in captured.captured_queries if "cms_cmsplugin" in query["sql"]]
        self.assertEqual(len(plugin_queries), 2)
        self.assertEqual(tree.token, queries.placeholder_token(placeholder, "en"))

    def test_plugin_tree_needs_read_access(self):
        with self.assertRaises(Placeholder.DoesNotExist):
            queries.get_plugin_tree(self.placeholder, "en", self.context_for(self._create_user("visitor")), admin=True)

    def test_token_follows_every_change(self):
        token = queries.placeholder_token(self.placeholder, "en")
        self.assertEqual(queries.placeholder_token(self.placeholder, "en"), token)

        changes = (
            lambda: plugin_services.move_plugin(self.reload(self.second), 1, context=self.context),
            lambda: plugin_services.change_plugin(self.reload(self.child), {"body": "changed"}, context=self.context),
            lambda: plugin_services.add_plugin(self.placeholder, "TextPlugin", "en", {"body": "x"}, context=self.context),
            lambda: plugin_services.delete_plugin(self.reload(self.child), context=self.context),
        )
        for change in changes:
            change()
            new_token = queries.placeholder_token(self.placeholder, "en")
            self.assertNotEqual(new_token, token)
            token = new_token

    def test_token_is_per_language(self):
        english = queries.placeholder_token(self.placeholder, "en")
        add_plugin(self.placeholder, "TextPlugin", "de", body="Hallo")

        self.assertEqual(queries.placeholder_token(self.placeholder, "en"), english)
        self.assertNotEqual(queries.placeholder_token(self.placeholder, None), english)

    # -- the stale-content check ---------------------------------------------

    def test_a_current_token_lets_the_write_through(self):
        token = queries.get_plugin_tree(self.placeholder, "en", self.context, admin=True).token

        plugin_services.move_plugin(self.reload(self.second), 1, context=self.context, expected_token=token)

        self.assertEqual(self.reload(self.second).position, 1)

    def test_a_stale_token_is_refused(self):
        token = queries.get_plugin_tree(self.placeholder, "en", self.context, admin=True).token
        # Another editor changes the placeholder in the meantime.
        plugin_services.change_plugin(self.reload(self.child), {"body": "theirs"}, context=self.context)

        verdict = can(operations.MOVE_PLUGIN, self.context, plugin=self.second, target_position=1, expected_token=token)
        self.assertEqual([(reason.name, reason.kind) for reason in verdict.reasons],
                         [("cms.core.content_unchanged", "policy")])
        self.assertEqual(verdict.skipped, [])
        with self.assertRaises(OperationBlocked):
            plugin_services.move_plugin(self.reload(self.second), 1, context=self.context, expected_token=token)
        self.assertEqual(self.reload(self.second).position, 3)

    def test_a_write_with_a_token_locks_the_placeholder(self):
        from django.db import connection as db
        from django.db.models.query import QuerySet

        locks = []
        original = QuerySet.select_for_update

        def select_for_update(queryset, *args, **kwargs):
            if queryset.model is Placeholder:
                locks.append(db.in_atomic_block)
            return original(queryset, *args, **kwargs)

        with patch.object(QuerySet, "select_for_update", autospec=True, side_effect=select_for_update):
            plugin_services.move_plugin(self.reload(self.second), 1, context=self.context)
            self.assertEqual(locks, [])  # no token: nothing to protect
            token = queries.get_plugin_tree(self.placeholder, "en", self.context, admin=True).token
            plugin_services.move_plugin(self.reload(self.second), 2, context=self.context, expected_token=token)
            self.assertEqual(locks, [True])  # inside the operation's transaction
            with patch.object(db, "in_atomic_block", False):
                # A dry run outside a transaction does not lock (and cannot).
                can(operations.MOVE_PLUGIN, self.context, plugin=self.second, target_position=1,
                    expected_token=token)
            self.assertEqual(locks, [True])

    def test_every_placeholder_writing_operation_takes_a_token(self):
        for operation_id in (
            operations.ADD_PLUGIN,
            operations.CHANGE_PLUGIN,
            operations.MOVE_PLUGIN,
            operations.CUT_PLUGIN,
            operations.DELETE_PLUGIN,
            operations.CLEAR_PLACEHOLDER,
            operations.PASTE_PLUGIN,
            operations.PASTE_PLACEHOLDER,
            operations.ADD_PLUGINS_FROM_PLACEHOLDER,
        ):
            with self.subTest(operation=operation_id):
                arguments = {argument.name: argument for argument in operations.get_operation(operation_id).arguments}
                self.assertFalse(arguments["expected_token"].required)

    def test_clear_with_a_stale_token_is_refused(self):
        token = queries.placeholder_token(self.placeholder, "en")
        add_plugin(self.placeholder, "TextPlugin", "en", body="late")

        with self.assertRaises(OperationBlocked):
            plugin_services.clear_placeholder(self.placeholder, "en", context=self.context, expected_token=token)
        self.assertEqual(self.placeholder.get_plugins("en").count(), 4)

    # -- the pilot path -------------------------------------------------------

    def test_pilot_path(self):
        """Look up, read, dry-run and move, as an MCP tool or REST endpoint would."""
        source = lookup("cms.pagecontent", self.content.pk, self.context, admin=True)
        placeholder = queries.get_placeholders(source, self.context, admin=True).get(slot="body")
        tree = queries.get_plugin_tree(placeholder, "en", self.context, admin=True)
        payload = {"plugin": tree.plugins[-1].pk, "target_position": 1, "expected_token": tree.token}

        move = operations.get_operation(operations.MOVE_PLUGIN)
        kwargs = {}
        for argument in move.arguments:
            if argument.name in payload:
                value = payload[argument.name]
                kwargs[argument.name] = lookup(argument.models[0], value, self.context, admin=True) if argument.models else value

        self.assertTrue(can(move.id, self.context, **kwargs))
        move.service(**kwargs, context=self.context)
        self.assertEqual(
            [plugin.pk for plugin in queries.get_plugin_tree(placeholder, "en", self.context, admin=True).plugins],
            [self.second.pk, self.first.pk, self.child.pk],
        )


class PublishedReadsTest(CMSTestCase):
    """``admin=False``, the default: what the site shows, to whoever may view it."""

    def setUp(self):
        super().setUp()
        self.page = create_page("Home", "nav_playground.html", "en")
        self.content = self.page.get_content_obj("en")
        self.placeholder = self.content.get_placeholders().get(slot="body")
        self.plugin = add_plugin(self.placeholder, "TextPlugin", "en", body="hello")
        self.anonymous = OperationContext(user=AnonymousUser(), language="en")

    def test_anonymous_visitors_read_a_public_page(self):
        for context in (self.anonymous, OperationContext(user=None, language="en")):
            with self.subTest(user=context.user):
                source = lookup("cms.pagecontent", self.content.pk, context)
                placeholder = queries.get_placeholders(source, context).get(slot="body")
                tree = queries.get_plugin_tree(placeholder, "en", context)

                self.assertEqual([plugin.pk for plugin in tree.plugins], [self.plugin.pk])
                self.assertEqual(lookup("cms.cmsplugin", self.plugin.pk, context).body, "hello")

    def test_a_page_requiring_login_is_hidden_from_visitors(self):
        self.page.login_required = True
        self.page.save()
        member = OperationContext(user=self._create_user("member"), language="en")

        with self.assertRaises(PageContent.DoesNotExist):
            lookup("cms.pagecontent", self.content.pk, self.anonymous)
        with self.assertRaises(Placeholder.DoesNotExist):
            lookup("cms.placeholder", self.placeholder.pk, self.anonymous)
        self.assertEqual(lookup("cms.pagecontent", self.content.pk, member), self.content)

    def test_published_reads_use_objects_and_editing_reads_admin_manager(self):
        # As with djangocms-versioning when the content has no published version:
        # ``objects`` does not return it, ``admin_manager`` does.
        editor = OperationContext(user=self.get_superuser(), language="en")
        with patch.object(PageContent.objects, "get_queryset", return_value=PageContent.admin_manager.none()):
            with self.assertRaises(PageContent.DoesNotExist):
                lookup("cms.pagecontent", self.content.pk, editor)
            with self.assertRaises(Placeholder.DoesNotExist):
                lookup("cms.placeholder", self.placeholder.pk, editor)
            with self.assertRaises(CMSPlugin.DoesNotExist):
                lookup("cms.cmsplugin", self.plugin.pk, editor)

            self.assertEqual(lookup("cms.pagecontent", self.content.pk, editor, admin=True), self.content)
            self.assertEqual(lookup("cms.placeholder", self.placeholder.pk, editor, admin=True), self.placeholder)

    def test_sources_without_a_view_hook_are_never_published(self):
        # A clipboard: even its owner does not read it as published content.
        owner = self.get_superuser()
        clipboard = Placeholder.objects.create(slot="clipboard")
        clipboard.source = UserSettings.objects.create(user=owner, language="en", clipboard=clipboard)
        clipboard.save()

        with self.assertRaises(Placeholder.DoesNotExist):
            lookup("cms.placeholder", clipboard.pk, OperationContext(user=owner, language="en"))
        self.assertEqual(
            lookup("cms.placeholder", clipboard.pk, OperationContext(user=owner, language="en"), admin=True), clipboard
        )


class PageReadsTest(CMSTestCase):
    """Page reads: by path, content with fallback, lists, trees and search, in both modes."""

    def setUp(self):
        from django.contrib.sites.models import Site

        super().setUp()
        self.site = Site.objects.get_current()
        self.home = create_page("Home", "nav_playground.html", "en")
        self.home.set_as_homepage()
        create_page_content("de", "Startseite", self.home)
        self.about = create_page("About", "nav_playground.html", "en", parent=self.home, slug="about")
        self.team = create_page("Team", "nav_playground.html", "en", parent=self.about, slug="team")
        self.members = create_page("Members", "nav_playground.html", "en", login_required=True, slug="members")
        self.page_type = create_page("Type", "nav_playground.html", "en", slug="type")
        self.page_type.is_page_type = True
        self.page_type.save()
        self.anonymous = OperationContext(user=AnonymousUser(), language="en")
        self.member = OperationContext(user=self._create_user("member"), language="en")
        self.editor = OperationContext(user=self.get_superuser(), language="en")

    def restrict(self, page):
        from cms.api import assign_user_to_page

        assign_user_to_page(page, self.member.user, can_view=True)

    # -- by path, by id ---------------------------------------------------------

    def test_page_by_path(self):
        self.assertEqual(page_queries.get_page_by_path(self.site, "", self.anonymous), self.home)
        self.assertEqual(page_queries.get_page_by_path(self.site, "/about/team/", self.anonymous), self.team)
        page = page_queries.get_page_by_path(self.site, "about", self.anonymous)
        self.assertEqual(page, self.about)
        self.assertIn("en", page.urls_cache)
        with self.assertRaises(Page.DoesNotExist):
            page_queries.get_page_by_path(self.site, "nowhere", self.anonymous)

    def test_view_restrictions_and_login_required(self):
        self.restrict(self.about)
        for path in ("about", "about/team", "members"):
            with self.subTest(path=path):
                with self.assertRaises(Page.DoesNotExist):
                    page_queries.get_page_by_path(self.site, path, self.anonymous)
                self.assertTrue(page_queries.get_page_by_path(self.site, path, self.member))
        with self.assertRaises(Page.DoesNotExist):
            lookup("cms.page", self.members.pk, self.anonymous)

    def test_editing_reads_are_for_staff(self):
        with self.assertRaises(Page.DoesNotExist):
            page_queries.get_page(self.about.pk, self.member, admin=True)
        self.assertEqual(page_queries.get_page(self.about.pk, self.editor, admin=True), self.about)

    def test_published_reads_use_objects(self):
        # As with djangocms-versioning when the page has no published version.
        with patch.object(PageContent.objects, "get_queryset", return_value=PageContent.admin_manager.none()):
            with self.assertRaises(Page.DoesNotExist):
                page_queries.get_page(self.about.pk, self.editor)
            self.assertEqual(page_queries.get_page(self.about.pk, self.editor, admin=True), self.about)
            self.assertEqual(page_queries.get_page_contents(self.site, "en", self.editor), [])
            self.assertTrue(page_queries.get_page_contents(self.site, "en", self.editor, admin=True))

    # -- content and fallback -------------------------------------------------

    def test_content_with_fallback(self):
        german = page_queries.get_page_content(self.home, "de", self.anonymous)
        fallback = page_queries.get_page_content(self.about, "de", self.anonymous)

        self.assertEqual((german.language, german.title), ("de", "Startseite"))
        self.assertEqual((fallback.language, fallback.title), ("en", "About"))
        with self.assertRaises(PageContent.DoesNotExist):
            page_queries.get_page_content(self.about, "de", self.anonymous, fallback=False)
        self.assertEqual(page_queries.get_page_content(self.about, "de", self.editor, admin=True).language, "en")

    def test_content_of_a_hidden_page(self):
        with self.assertRaises(PageContent.DoesNotExist):
            page_queries.get_page_content(self.members, "en", self.anonymous)

    # -- lists and trees --------------------------------------------------------

    def test_page_contents_in_tree_order_one_per_page(self):
        contents = page_queries.get_page_contents(self.site, "de", self.member)

        self.assertEqual(
            [(content.page, content.language) for content in contents],
            [(self.home, "de"), (self.about, "en"), (self.team, "en"), (self.members, "en")],
        )
        self.assertEqual(
            [content.page for content in page_queries.get_page_contents(self.site, "de", self.member, fallback=False)],
            [self.home],
        )

    def test_lists_leave_out_what_the_user_may_not_read(self):
        self.restrict(self.about)

        self.assertEqual(
            [content.page for content in page_queries.get_page_contents(self.site, "en", self.anonymous)], [self.home]
        )
        self.assertEqual(page_queries.get_page_contents(self.site, "en", self.member, admin=True), [])

    def test_lists_take_a_fixed_number_of_queries(self):
        page_queries.get_page_contents(self.site, "en", self.member)  # warm caches
        with CaptureQueriesContext(connection) as few:
            page_queries.get_page_contents(self.site, "en", self.member)
        for i in range(10):
            create_page(f"More {i}", "nav_playground.html", "en", parent=self.about)
        with CaptureQueriesContext(connection) as many:
            contents = page_queries.get_page_contents(self.site, "en", self.member)

        self.assertEqual(len(contents), 14)
        self.assertEqual(len(many.captured_queries), len(few.captured_queries))

    def test_page_tree(self):
        tree = page_queries.get_page_tree(self.site, "en", self.member)

        self.assertEqual([node.page for node in tree], [self.home, self.members])
        self.assertEqual([node.page for node in tree[0].children], [self.about])
        self.assertEqual([node.page for node in tree[0].children[0].children], [self.team])

    def test_a_hidden_parent_hides_its_subtree(self):
        self.restrict(self.about)
        tree = page_queries.get_page_tree(self.site, "en", self.anonymous)

        self.assertEqual([node.page for node in tree], [self.home])
        self.assertEqual(tree[0].children, [])

    # -- search -------------------------------------------------------------------

    def test_search(self):
        add_plugin(self.team.get_content_obj("en").get_placeholders().get(slot="body"), "TextPlugin", "en",
                   body="Our team of gardeners")

        def found(q, language="en", context=None):
            contents = page_queries.search_pages(self.site, q, language, context or self.anonymous)
            return [content.page for content in contents]

        self.assertEqual(found("about"), [self.about])  # title
        self.assertEqual(found("GARDEN"), [self.team])  # plugin search_fields, case-insensitive
        self.assertEqual(found("Startseite", "de"), [self.home])
        self.assertEqual(found("Startseite"), [])  # another language's title
        self.assertEqual(found("type"), [])  # page types are left out
        self.assertEqual(found(""), [])
        self.assertEqual(found("members"), [])  # login required
        self.assertEqual(found("members", context=self.member), [self.members])

    # -- declarations ---------------------------------------------------------------

    def test_page_reads_are_declared_with_lookups_for_their_models(self):
        from cms import operations as operation_registry
        from cms.shared.lookups import get_lookup

        for query_id in ("get_page", "get_page_by_path", "get_page_content", "get_page_content_by_path",
                         "get_page_contents",
                         "get_page_tree", "search_pages"):
            query = operation_registry.get_query(query_id)
            with self.subTest(query=query_id):
                self.assertEqual(query.modes, ("published", "editing"))
                for argument in query.arguments:
                    for label in argument.models:
                        get_lookup(label)

    def test_restrictions_on_ancestors_outside_the_list_apply(self):
        # The menu passes only pages with content in its languages; a restricted
        # ancestor without such content must still restrict its descendants.
        from cms.permissions.page_permissions import filter_viewable_page_contents

        self.restrict(self.about)
        team = self.team.get_content_obj("en")

        self.assertEqual(filter_viewable_page_contents(AnonymousUser(), [team], self.site), [])
        self.assertEqual(filter_viewable_page_contents(self.member.user, [team], self.site), [team])

    def test_search_only_matches_public_content(self):
        # As with djangocms-versioning when "About" is only in a draft: the
        # public content does not include it.
        draft = self.about.get_content_obj("en")
        public = PageContent.admin_manager.exclude(pk=draft.pk)
        with patch.object(PageContent.objects, "get_queryset", return_value=public):
            self.assertFalse(Page.objects.search("about").exists())
            self.assertEqual(page_queries.search_pages(self.site, "about", "en", self.anonymous), [])
            self.assertEqual(
                [content.page for content in page_queries.search_pages(self.site, "about", "en", self.editor,
                                                                        admin=True)],
                [self.about],
            )
        self.assertEqual(list(Page.objects.search("about")), [self.about])

    # -- review fixes -----------------------------------------------------------------

    def test_published_content_ignores_the_page_caches(self):
        # Whatever filled the page's caches -- here, content the public manager
        # does not return, as a draft under djangocms-versioning -- must not leak.
        draft = self.about.get_content_obj("en")
        public = PageContent.admin_manager.exclude(pk=draft.pk)
        page = Page.objects.get(pk=self.about.pk)
        page.page_content_cache = {"en": draft}
        page.admin_content_cache = {}
        with patch.object(PageContent.objects, "get_queryset", return_value=public):
            with self.assertRaises(PageContent.DoesNotExist):
                page_queries.get_page_content(page, "en", self.editor)
            # The editing read is not fooled by an empty admin cache either.
            self.assertEqual(page_queries.get_page_content(page, "en", self.editor, admin=True), draft)

    def test_editors_who_may_change_a_restricted_page_may_read_it(self):
        from django.contrib.auth.models import Permission

        from cms.api import assign_user_to_page
        from cms.permissions.page_permissions import user_can_view_page

        self.restrict(self.about)  # viewable by member only
        editor = self._create_user("editor", is_staff=True)
        editor.user_permissions.add(Permission.objects.get(codename="change_page"))
        assign_user_to_page(self.about, editor, can_change=True)
        editor = type(editor).objects.get(pk=editor.pk)
        context = OperationContext(user=editor, language="en")
        self.assertTrue(user_can_view_page(editor, self.about))

        self.assertEqual(page_queries.get_page(self.about.pk, context, admin=True), self.about)
        self.assertEqual(page_queries.get_page(self.team.pk, context), self.team)
        self.assertIn(self.about, [c.page for c in page_queries.get_page_contents(self.site, "en", context, admin=True)])
        # The same rule as the core reads, which ask the page's own view permission.
        self.assertTrue(queries.get_placeholders(self.about.get_content_obj("en"), context, admin=True))
        # And still not for someone with change permission elsewhere only.
        other = self._create_user("other", is_staff=True)
        other.user_permissions.add(Permission.objects.get(codename="change_page"))
        assign_user_to_page(self.members, other, can_change=True)
        other = type(other).objects.get(pk=other.pk)
        with self.assertRaises(Page.DoesNotExist):
            page_queries.get_page(self.about.pk, OperationContext(user=other, language="en"), admin=True)

    def test_shared_path_in_different_languages(self):
        # Page A is "shared" in English, page B is "shared" in German.
        a = create_page("A", "nav_playground.html", "en", slug="shared")
        create_page_content("de", "A de", a, slug="a-de")
        b = create_page("B", "nav_playground.html", "en", slug="bee")
        create_page_content("de", "B de", b, slug="shared")

        page = page_queries.get_page_by_path(self.site, "shared", self.anonymous)
        self.assertEqual(page, a)
        self.assertEqual({url.page_id for url in page.urls_cache.values()}, {a.pk})
        self.assertEqual(page.get_path("de"), "a-de")

        page = page_queries.get_page_by_path(self.site, "shared", self.anonymous, language="de")
        self.assertEqual(page, b)
        self.assertEqual(page.get_path("en"), "bee")

    def test_page_view_resolves_shared_paths_by_request_language(self):
        from cms.pages.utils import get_page_from_request

        a = create_page("A", "nav_playground.html", "en", slug="shared")
        create_page_content("de", "A de", a, slug="a-de")
        b = create_page("B", "nav_playground.html", "en", slug="bee")
        create_page_content("de", "B de", b, slug="shared")

        # LocaleMiddleware activates the request's language in the page view.
        with override("de"):
            german = get_page_from_request(self.get_request("/de/shared/", "de"), use_path="shared")
        with override("en"):
            english = get_page_from_request(self.get_request("/en/shared/", "en"), use_path="shared")

        self.assertEqual((german, english), (b, a))
        self.assertEqual(german.get_path("en"), "bee")
        self.assertEqual(english.get_path("de"), "a-de")

    # -- path to content ---------------------------------------------------------------

    def test_content_by_path(self):
        home = page_queries.get_page_content_by_path(self.site, "", "de", self.anonymous)
        team = page_queries.get_page_content_by_path(self.site, "/about/team/", "de", self.anonymous)

        self.assertEqual((home.page, home.language, home.title), (self.home, "de", "Startseite"))
        self.assertEqual((team.page, team.language), (self.team, "en"))  # fallback
        self.assertIn("en", team.page.urls_cache)
        with self.assertRaises(PageContent.DoesNotExist):
            page_queries.get_page_content_by_path(self.site, "about/team", "de", self.anonymous, fallback=False)
        with self.assertRaises(PageContent.DoesNotExist):
            page_queries.get_page_content_by_path(self.site, "nowhere", "en", self.anonymous)

    def test_content_by_path_applies_visibility(self):
        self.restrict(self.about)
        for path in ("about", "about/team", "members"):
            with self.subTest(path=path):
                with self.assertRaises(PageContent.DoesNotExist):
                    page_queries.get_page_content_by_path(self.site, path, "en", self.anonymous)
                self.assertTrue(page_queries.get_page_content_by_path(self.site, path, "en", self.member))
        with self.assertRaises(PageContent.DoesNotExist):
            page_queries.get_page_content_by_path(self.site, "about", "en", self.member, admin=True)  # not staff

    def test_content_by_path_reads_through_the_mode(self):
        draft = self.about.get_content_obj("en")
        public = PageContent.admin_manager.exclude(pk=draft.pk)
        with patch.object(PageContent.objects, "get_queryset", return_value=public):
            with self.assertRaises(PageContent.DoesNotExist):
                page_queries.get_page_content_by_path(self.site, "about", "en", self.editor)
            self.assertEqual(
                page_queries.get_page_content_by_path(self.site, "about", "en", self.editor, admin=True), draft
            )

    def test_content_by_path_with_a_shared_path(self):
        a = create_page("A", "nav_playground.html", "en", slug="shared")
        create_page_content("de", "A de", a, slug="a-de")
        b = create_page("B", "nav_playground.html", "en", slug="bee")
        create_page_content("de", "B de", b, slug="shared")

        german = page_queries.get_page_content_by_path(self.site, "shared", "de", self.anonymous)
        english = page_queries.get_page_content_by_path(self.site, "shared", "en", self.anonymous)

        self.assertEqual((german.page, german.title), (b, "B de"))
        self.assertEqual((english.page, english.title), (a, "A"))
        self.assertEqual(german.page.get_path("en"), "bee")
        self.assertEqual(english.page.get_path("de"), "a-de")

    def test_content_by_path_reads_less_than_two_calls(self):
        page_queries.get_page_content_by_path(self.site, "about/team", "de", self.member)  # warm caches
        with CaptureQueriesContext(connection) as combined:
            page_queries.get_page_content_by_path(self.site, "about/team", "de", self.member)
        with CaptureQueriesContext(connection) as chained:
            page = page_queries.get_page_by_path(self.site, "about/team", self.member, language="de")
            page_queries.get_page_content(page, "de", self.member)

        self.assertLess(len(combined.captured_queries), len(chained.captured_queries))

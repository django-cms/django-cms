# -*- coding: utf-8 -*-
from cms.tests.admin import AdminTestCase
from cms.tests.apphooks import ApphooksTestCase
from cms.tests.docs import DocsTestCase
from cms.tests.menu import FixturesMenuTests, MenuTests, AdvancedSoftrootTests
from cms.tests.navextender import NavExtenderTestCase
from cms.tests.nonroot import NonRootCase
from cms.tests.page import PagesTestCase, NoAdminPageTests
from cms.tests.permmod import PermissionModeratorTestCase
from cms.tests.placeholder import PlaceholderTestCase, PlaceholderActionTests
from cms.tests.placeholder import PlaceholderModelTests
from cms.tests.plugins import PluginManyToManyTestCase, PluginsTestCase
from cms.tests.rendering import RenderingTestCase
from cms.tests.reversion_tests import ReversionTestCase
from cms.tests.site import SiteTestCase
from cms.tests.urlutils import UrlutilsTestCase
from cms.tests.publisher import PublisherTestCase
from cms.tests.multilingual import MultilingualTestCase
from cms.tests.mail import MailTestCase
from cms.tests.settings import SettingsTests
from cms.tests.forms import FormsTestCase
from cms.tests.toolbar import ToolbarTests
from cms.tests.middleware import MiddlewareTestCase
from cms.tests.views import ViewTests
try:
    from cms.tests.javascript import JavascriptTestCase
except ImportError:
    import warnings
    import traceback
    exc = traceback.format_exc()
    warnings.warn("JavascriptTestCase cannot be run: %s" % exc)
    
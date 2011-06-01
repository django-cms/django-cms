# -*- coding: utf-8 -*-
<<<<<<< HEAD
from cms.tests.admin import *
from cms.tests.api import *
from cms.tests.apphooks import *
from cms.tests.docs import *
from cms.tests.forms import *
from cms.tests.mail import *
from cms.tests.menu import *
from cms.tests.menu_utils import *
from cms.tests.middleware import *
from cms.tests.multilingual import *
from cms.tests.navextender import *
from cms.tests.nonroot import *
from cms.tests.page import *
from cms.tests.permmod import *
from cms.tests.placeholder import *
from cms.tests.plugins import *
from cms.tests.po import *
from cms.tests.publisher import *
from cms.tests.rendering import *
from cms.tests.reversion_tests import *
from cms.tests.security import *
from cms.tests.settings import *
from cms.tests.site import *
from cms.tests.templatetags import *
from cms.tests.toolbar import *
from cms.tests.urlutils import *
from cms.tests.views import *
from cms.tests.management import *
=======
from cms.tests.admin import (AdminTestCase, AdminFieldsetTests, 
    AdminListFilterTests, AdminTests, NoDBAdminTests, PluginPermissionTests)
from cms.tests.api import PythonAPITests
from cms.tests.apphooks import ApphooksTestCase
from cms.tests.docs import DocsTestCase
from cms.tests.forms import FormsTestCase
from cms.tests.mail import MailTestCase
from cms.tests.menu import (FixturesMenuTests, MenuTests, AdvancedSoftrootTests, 
    ShowSubMenuCheck)
from cms.tests.menu_utils import MenuUtilsTests
from cms.tests.middleware import MiddlewareTestCase
from cms.tests.multilingual import MultilingualTestCase
from cms.tests.navextender import NavExtenderTestCase
from cms.tests.nonroot import NonRootCase
from cms.tests.page import PagesTestCase, NoAdminPageTests
from cms.tests.permmod import PermissionModeratorTests, PatricksMoveTest
from cms.tests.placeholder import (PlaceholderModelTests, PlaceholderAdminTest, 
    PlaceholderTestCase, PlaceholderActionTests)
from cms.tests.plugins import (PluginManyToManyTestCase, PluginsTestCase, 
    SekizaiTests, LinkPluginTestCase)
from cms.tests.po import PoTest
from cms.tests.publisher import PublisherTestCase
from cms.tests.rendering import RenderingTestCase
from cms.tests.reversion_tests import ReversionTestCase
from cms.tests.security import SecurityTests
from cms.tests.settings import SettingsTests
from cms.tests.site import SiteTestCase
from cms.tests.templatetags import TemplatetagTests, TemplatetagDatabaseTests
from cms.tests.toolbar import ToolbarTests
from cms.tests.urlutils import UrlutilsTestCase
from cms.tests.views import ViewTests
from cms.tests.management import ManagementTestCase

try:
    from cms.tests.javascript import JavascriptTestCase
except ImportError:
    import warnings
    import traceback
    exc = traceback.format_exc()
    warnings.warn("JavascriptTestCase cannot be run: %s" % exc)
>>>>>>> Made PageAdmin.add_plugin check add permissions for the actual plugin model


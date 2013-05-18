########################
Testing Your Extenstions
########################

************
Testing Apps
************

Your apps need testing, but in your live site they aren't in ``urls.py`` as they
are attached to a CMS page.  So if you want to be able to use ``reverse`` in
your tests, or test templates that use the ``url`` template tag, you need to
hook up your app to a special test version of ``urls.py`` and tell your tests
to use that.

So you could create ``myapp/tests/test_urls.py`` with the following code::

    from django.contrib import admin
    from django.conf.urls import url, patterns, include

    urlpatterns = patterns('',
        url(r'^admin/', include(admin.site.urls)),
        url(r'^myapp/', include('myapp.urls')),
        url(r'', include('cms.urls')),
    )

And then in your tests you can plug this in with::

    from cms.test_utils.util.context_managers import SettingsOverride
    from cms.test_utils.testcases import CMSTestCase

    class MyappTests(CMSTestCase):

        def test_myapp_page(self):
            with SettingsOverride(ROOT_URLCONF='myapp.tests.test_urls'):
                test_url = reverse('myapp_view_name')
                # rest of test as normal

If you want to the test url conf throughout your test class, then you can use
the ``SettingsOverrideTestCase``::

    from cms.test_utils.testcases import SettingsOverrideTestCase

    class MyappTests(SettingsOverrideTestCase):

        settings_overrides = {'ROOT_URLCONF': 'myapp.tests.test_urls'}

        def test_myapp_page(self):
            test_url = reverse('myapp_view_name')
            # rest of test as normal

***************
Testing Plugins
***************

Plugins can just be created as objects and then have methods called on them.
So you could do::

    from django.test import TestCase
    from myapp.cms_plugins import MyPlugin
    from myapp.models import MyappPlugin as MyappPluginModel

    class MypluginTests(TestCase):

        def setUp(self):
            self.plugin = MyPlugin()
            self.plugin.save()

        def test_plugin(self):
            context = {'info': 'value'}
            instance = MyappPluginModel(num_items=3)
            rendered_html = self.plugin.render(context, instance, None)
            self.assertIn('string', rendered_html)

Sometimes you might want to add a placeholder - say to check how the plugin
renders when it is in different size placeholders.  In that case you can create
the placeholder directly and pass it in::

    from django.test import TestCase
    from cms.api import add_plugin
    from myapp.cms_plugins import MyPlugin
    from myapp.models import MyappPlugin as MyappPluginModel

    class ImageSetTypePluginMixinContainerWidthTests(TestCase):
        def setUp(self):
            self.placeholder = Placeholder(slot=u"some_slot")
            self.placeholder.save()
            self.plugin = add_plugin(
                self.placeholder,
                u"MyPlugin",
                u"en",
                num_items=3,
            )

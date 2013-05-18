########################
Testing Your Extenstions
########################

************
testing apps
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

    class MyappTestCase(CMSTestCase):

        def test_myapp_page(self):
            with SettingsOverride(ROOT_URLCONF='myapp.tests.test_urls'):
                test_url = reverse('myapp_view_name')
                # rest of test as normal

If you want to the test url conf throughout your test class, then you can use
the ``SettingsOverrideTestCase``::

    from cms.test_utils.testcases import SettingsOverrideTestCase

    class MyappTestCase(SettingsOverrideTestCase):

        settings_overrides = {'ROOT_URLCONF': 'myapp.tests.test_urls'}

        def test_myapp_page(self):
            test_url = reverse('myapp_view_name')
            # rest of test as normal

***************
testing plugins
***************

************
testing menu
************

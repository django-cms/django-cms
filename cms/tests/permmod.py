from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from cms import settings as cms_settings
from cms.tests.base import PageBaseTestCase, URL_CMS_PAGE_ADD, URL_CMS_PAGE
from cms.models import Title, Page


class PermissionModeratorTestCase(PageBaseTestCase):
    """Permissions and moderator together
    
    Fixtures contains 3 users and 1 published page and some other stuff
    
    Users:
        1. `super`: superuser
        2. `master`: user with permissions to all aplications
        3.`slave`: user assigned to page `slave-home` can add/change/delete page
    
    Pages:
        1.`slave-home`: 
            - published page
            - assigned slave user which can add/change/delete this page and its descendants
            - `master` user want to moderate this page and all descendants
    
    """
    
    fixtures = ['../cms/tests/fixtures/permission.json']
    
    
    def setUp(self):
        self.user_super = User.objects.get(username="super")
        self.user_master = User.objects.get(username="master")
        self.user_slave = User.objects.get(username="slave")
    
    def test_00_configuration(self):
        """Just check if we have right configuration for this test. Problem lies
        in cms_settings!! something like cms_settings.CMS_MODERATOR = True just
        doesn't work!!!
        
        TODO: settings must be changed to be configurable / overridable
        """
        
        assert(cms_settings.CMS_PERMISSION)
        assert(cms_settings.CMS_MODERATOR)
    
    # helpers    
    
    def _add_page(self, user):
        """Helper for accessing new page creation
        """
        self._login_user(user)
        return self.client.get('/admin/cms/page/add/')
    
    def assertObjectExist(self, qs, **filter):
        try:
            return qs.get(**filter) 
        except ObjectDoesNotExist:
            pass
        raise self.failureException, "ObjectDoesNotExist raised"
    
    def assertObjectDoesNotExist(self, qs, **filter):
        try:
            qs.get(**filter) 
        except ObjectDoesNotExist:
            return
        raise self.failureException, "ObjectDoesNotExist not raised"
    
    @property
    def slave_page(self):
        return Page.objects.get(title_set__slug="slave-home")
    
    # tests
    
    def test_01_super_can_add_page_to_root(self, status_code=200):
        self.login_user(self.user_super)
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
    
    def test_02_master_can_add_page_to_root(self, status_code=200):
        self.login_user(self.user_master)
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
        
    def test_03_slave_can_add_page_to_root(self, status_code=403):
        self.login_user(self.user_slave)
        response = self.client.get(URL_CMS_PAGE_ADD)
        self.assertEqual(response.status_code, status_code)
    
    def test_04_moderation_on_slave_home(self):
        assert(self.slave_page.get_moderator_queryset().count()==1)
    
    
    def test_05_slave_can_add_page_under_slave_home(self):
        self.login_user(self.user_slave)
        slave_page = self.slave_page
        page_data = self.get_new_page_data()
        
        # reuest moderation
        page_data['moderator_state'] = Page.MODERATOR_NEED_APPROVEMENT
        page_data['moderator_message'] = "Approve me!"
        
        # add page
        url = URL_CMS_PAGE_ADD + "?target=%d&position=first-child" % slave_page.pk
        response = self.client.post(url, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        # public model shouldn't be available yet, because of the moderation
        self.assertObjectExist(Title.objects, slug=page_data['slug'])
        self.assertObjectDoesNotExist(Title.PublicModel.objects, slug=page_data['slug'])
        
        # page created?
        page = self.assertObjectExist(Page.objects, title_set__slug=page_data['slug'])
        # moderators and approvemnt right?
        assert(page.get_moderator_queryset().count()==1)
        assert(page.moderator_state == Page.MODERATOR_NEED_APPROVEMENT)
        
        # must not have public object yet
        assert(not page.public)
        
        # publish / approve page by master
        self.login_user(self.user_master)
        response = self.client.get(URL_CMS_PAGE + "%d/approve/" % page.pk)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        # reload page
        page = self.assertObjectExist(Page.objects, title_set__slug=page_data['slug'])        
        
        # must have public object now
        assert(page.public)
        # and public object must be published
        assert(page.public.published)  
        
    def _add_plugin(self, user):
        slave_page = self.slave_page
        
        post_data = {
            'language': 'en',
            'page_id': slave_page.pk,
            'placeholder': 'Right-Column',
            'plugin_type': 'TextPlugin'
        }
        self.login_user(user)
        url = URL_CMS_PAGE + "%d/add-plugin/" % slave_page.pk
        response = self.client.post(url, post_data)
        assert(response.content == "1")
    
    def test_06_super_can_add_plugin(self):
        self._add_plugin(self.user_super)
    
    def test_07_master_can_add_plugin(self):
        self._add_plugin(self.user_master)
        
    def test_08_slave_can_add_plugin(self):
        self._add_plugin(self.user_slave)
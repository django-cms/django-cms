import copy
from django.conf import settings
from django.test.testcases import TestCase
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import slugify
from cms.models import Title, Page

URL_CMS_PAGE = "/admin/cms/page/"
URL_CMS_PAGE_ADD = URL_CMS_PAGE + "add/"
URL_CMS_PAGE_CHANGE = URL_CMS_PAGE + "%d/" 
URL_CMS_PLUGIN_ADD = URL_CMS_PAGE + "add-plugin/"
URL_CMS_PLUGIN_EDIT = URL_CMS_PAGE + "edit-plugin/"

class CMSTestCase(TestCase):
    counter = 1
        
    def _pre_setup(self):
        """We are doing a lot of setting modifications in our tests, this 
        mechanism will restore to original settings after each test case.
        """
        super(CMSTestCase, self)._pre_setup()
        
        # backup settings
        self._original_settings_wrapped = copy.deepcopy(settings._wrapped) 
        
    def _post_teardown(self):
        # restore original settings after each test
        settings._wrapped = self._original_settings_wrapped
        super(CMSTestCase, self)._post_teardown()
    
        
    def login_user(self, user):
        logged_in = self.client.login(username=user.username, password=user.username)
        self.assertEqual(logged_in, True)
    
    
    def get_new_page_data(self, parent_id=''):
        page_data = {'title':'test page %d' % self.counter, 
            'slug':'test-page-%d' % self.counter, 'language':settings.LANGUAGES[0][0],
            'site':1, 'template':'index.html', 'parent': parent_id}
        
        # required only if user haves can_change_permission
        page_data['pagepermission_set-TOTAL_FORMS'] = 0
        page_data['pagepermission_set-INITIAL_FORMS'] = 0
        page_data['pagepermission_set-MAX_NUM_FORMS'] = 0
        
        self.counter = self.counter + 1
        return page_data
    
    def print_page_structure(self, title=None):
        """Just a helper to see the page struct.
        """
        print "-------------------------- %s --------------------------------" % (title or "page structure")
        for page in Page.objects.drafts().order_by('tree_id', 'parent', 'lft'):
            print "%s%s #%d" % ("    " * (page.level), page, page.id)
    
    
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
    
    def create_page(self, parent_page=None, user=None, position="last-child", title=None, site=1):
        """Common way for page creation with some checks
        """
        if user:
            # change logged in user
            self.login_user(user)
        
        parent_id = ''
        if parent_page:
            parent_id=parent_page.id
            
        page_data = self.get_new_page_data(parent_id)
        page_data['site'] = site
        
        page_data.update({
            '_save': 'Save',
        })
        
        if title is not None:
            page_data['title'] = title
            page_data['slug'] = slugify(title)
        
        # add page
        if parent_page:
            url = URL_CMS_PAGE_ADD + "?target=%d&position=%s" % (parent_page.pk, position)
        else:
            url = URL_CMS_PAGE_ADD
        response = self.client.post(url, page_data)
        self.assertRedirects(response, URL_CMS_PAGE)
        
        # check existence / get page
        page = self.assertObjectExist(Page.objects, title_set__slug=page_data['slug'])
        self.assertEqual(page.site_id, site)
        
        # public model shouldn't be available yet, because of the moderation
        self.assertObjectExist(Title.objects, slug=page_data['slug'])
        
        if settings.CMS_MODERATOR and page.is_under_moderation(): 
            self.assertObjectDoesNotExist(Title.objects.public(), slug=page_data['slug'])
        
        return page
    
    
    def copy_page(self, page, target_page):
        from cms.utils.page import get_available_slug
        
        data = {
            'position': 'last-child',
            'target': target_page.pk,
            'site': 1,
            'copy_permissions': 'on',
            'copy_moderation': 'on',
        }
        
        response = self.client.post(URL_CMS_PAGE + "%d/copy-page/" % page.pk, data)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, "ok")
        
        title = page.title_set.all()[0] 
        copied_slug = get_available_slug(title)
        
        copied_page = self.assertObjectExist(Page.objects, title_set__slug=copied_slug, parent=target_page)
        return copied_page
    
    
    def move_page(self, page, target_page, position="first-child"):       
        data = {
            'position': position,
            'target': target_page.pk,
        }
        response = self.client.post(URL_CMS_PAGE + "%d/move-page/" % page.pk, data)
        self.assertEqual(response.status_code, 200)        
        return self.reload_page(page)
        
        
    def reload_page(self, page):
        """Helper for page reload with check. Usefull, when something on page
        gets changed because of the previous action, we need to take it again
        from db, otherwise we just have old version.
        """
        page = self.assertObjectExist(Page.objects, id=page.pk)
        return page    
        
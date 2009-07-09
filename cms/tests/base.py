from django.test.testcases import TestCase

URL_CMS_PAGE = "/admin/cms/page/"
URL_CMS_PAGE_ADD = URL_CMS_PAGE + "add/"

class PageBaseTestCase(TestCase):
    counter = 1
    
    def login_user(self, user):
        logged_in = self.client.login(username=user.username, password=user.username)
        assert logged_in
    
    def get_new_page_data(self):
        page_data = {'title':'test page %d' % self.counter, 
            'slug':'test-page-%d' % self.counter, 'language':'en',
            'site':1, 'template':'index.html'}
        
        # required only if user haves can_change_permission
        #page_data['pagepermission_set-TOTAL_FORMS'] = 0
        #page_data['pagepermission_set-INITIAL_FORMS'] = 0
        
        self.counter = self.counter + 1
        return page_data

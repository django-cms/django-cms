from cms.models import Title, Page
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.core.urlresolvers import reverse
from django.template.context import Context
from django.template.defaultfilters import slugify
from django.test.testcases import TestCase
import copy
import sys
import urllib
import warnings

URL_CMS_PAGE = "/admin/cms/page/"
URL_CMS_PAGE_ADD = URL_CMS_PAGE + "add/"
URL_CMS_PAGE_CHANGE = URL_CMS_PAGE + "%d/" 
URL_CMS_PLUGIN_ADD = URL_CMS_PAGE + "add-plugin/"
URL_CMS_PLUGIN_EDIT = URL_CMS_PAGE + "edit-plugin/"
URL_CMS_PLUGIN_REMOVE = URL_CMS_PAGE + "remove-plugin/"

class _Warning(object):
    def __init__(self, message, category, filename, lineno):
        self.message = message
        self.category = category
        self.filename = filename
        self.lineno = lineno



def _collectWarnings(observeWarning, f, *args, **kwargs):
    def showWarning(message, category, filename, lineno, file=None, line=None):
        assert isinstance(message, Warning)
        observeWarning(_Warning(
                message.args[0], category, filename, lineno))

    # Disable the per-module cache for every module otherwise if the warning
    # which the caller is expecting us to collect was already emitted it won't
    # be re-emitted by the call to f which happens below.
    for v in sys.modules.itervalues():
        if v is not None:
            try:
                v.__warningregistry__ = None
            except:
                # Don't specify a particular exception type to handle in case
                # some wacky object raises some wacky exception in response to
                # the setattr attempt.
                pass

    origFilters = warnings.filters[:]
    origShow = warnings.showwarning
    warnings.simplefilter('always')
    try:
        warnings.showwarning = showWarning
        result = f(*args, **kwargs)
    finally:
        warnings.filters[:] = origFilters
        warnings.showwarning = origShow
    return result

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
        self.user = user
        self.assertEqual(logged_in, True)
    
    
    def get_new_page_data(self, parent_id=''):
        page_data = {'title':'test page %d' % self.counter, 
            'slug':'test-page-%d' % self.counter, 'language':settings.LANGUAGES[0][0],
            'site':1, 'template':'nav_playground.html', 'parent': parent_id}
        
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
    
    def create_page(self, parent_page=None, user=None, position="last-child", title=None, site=1, published=False, in_navigation=False):
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
        page_data['published'] = published
        page_data['in_navigation'] = in_navigation
        if settings.CMS_SITE_LANGUAGES.get(site, False):
            page_data['language'] = settings.CMS_SITE_LANGUAGES[site][0]
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
        
# test case currently failing because Title model is no longer under Publisher
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
    
    def get_pages_root(self):
        return urllib.unquote(reverse("pages-root"))
        
    def get_context(self, path=None):
        if not path:
            path = self.get_pages_root()
        context = {}
        request = self.get_request(path)
        
        context['request'] = request
        
        return Context(context)   
        
    def get_request(self, path=None):
        if not path:
            path = self.get_pages_root()

        environ = {
            'HTTP_COOKIE':      self.client.cookies,
            'PATH_INFO':         path,
            'QUERY_STRING':      '',
            'REMOTE_ADDR':       '127.0.0.1',
            'REQUEST_METHOD':    'GET',
            'SCRIPT_NAME':       '',
            'SERVER_NAME':       'testserver',
            'SERVER_PORT':       '80',
            'SERVER_PROTOCOL':   'HTTP/1.1',
            'wsgi.version':      (1,0),
            'wsgi.url_scheme':   'http',
            'wsgi.errors':       self.client.errors,
            'wsgi.multiprocess': True,
            'wsgi.multithread':  False,
            'wsgi.run_once':     False,
        }
        request = WSGIRequest(environ)
        request.session = self.client.session
        request.user = self.user
        request.LANGUAGE_CODE = settings.LANGUAGES[0][0]
        return request
        
        
    def failUnlessWarns(self, category, message, f, *args, **kwargs):
        warningsShown = []
        result = _collectWarnings(warningsShown.append, f, *args, **kwargs)

        if not warningsShown:
            self.fail("No warnings emitted")
        first = warningsShown[0]
        for other in warningsShown[1:]:
            if ((other.message, other.category)
                != (first.message, first.category)):
                self.fail("Can't handle different warnings")
        self.assertEqual(first.message, message)
        self.assertTrue(first.category is category)

        return result
    assertWarns = failUnlessWarns
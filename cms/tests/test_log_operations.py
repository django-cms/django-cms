from django.contrib.admin.models import LogEntry

from cms.api import create_page
from cms.test_utils.testcases import (
    CMSTestCase, URL_CMS_PAGE_MOVE,
    URL_CMS_PAGE_CHANGE, URL_CMS_PAGE_ADD,
)
from cms.models.pagemodel import Page
from cms.forms.wizards import CreateCMSPageForm
from cms.wizards.forms import step2_form_factory, WizardStep2BaseForm


from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION

"""
Make sure that only one entry is created for each action, for example when a page is moved it is deleted and recreated!!

Dev helper code FIXME: REMOVEME:
    log_entries = LogEntry.objects.all()
    entry = LogEntry.objects.filter(user=user, object_id=instance_id, action_flag__in=(CHANGE,))[0]
    Check id's match in log self.assertEqual(page_data.pk, int(LogEntry.objects.all()[0].object_id))

TODO: Test the correct flag is set!!

Log messages are inconsistent atm regarding what's set for Move, Change and Delete messages
"""

# Snippet taken from: test_wizards.py
CreateCMSPageForm = step2_form_factory(
    mixin_cls=WizardStep2BaseForm,
    entry_form_class=CreateCMSPageForm,
)


class LogPageOperationsTests(CMSTestCase):

    def setUp(self):
        pass

    def test_log_for_create_admin_page(self):
        """
        Test that when a page is created on the UI using the page admin a log entry is created.
        """

        page_data = self.get_new_page_data()
        superuser = self.get_superuser()

        with self.login_user_context(superuser):

            page_one_response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            page_one = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)

            # Check to see if the page added log entry exists
            self.assertEqual(1, LogEntry.objects.count())

            # Check that the contents of the log is correct
            log_entry = LogEntry.objects.all()[0]
            message = '[{"added": {}}]'
            self.assertEqual(message, log_entry.change_message)

            # Check the action flag is set correctly
            self.assertEqual(ADDITION, log_entry.action_flag)

    def test_log_for_create_wizard_page(self):
        """
        Test that when a page is created via the create page wizard UI a log entry is created.
        """

        superuser = self.get_superuser()
        data = {
            'title': 'page 1',
            'slug': 'page_1',
            'page_type': None,
        }
        form = CreateCMSPageForm(
            data=data,
            wizard_page=None,
            wizard_user=superuser,
            wizard_language='en',
        )
        self.assertTrue(form.is_valid())
        page = form.save()

        with self.login_user_context(superuser):

            # Check to see if the page added log entry exists
            self.assertEqual(1, LogEntry.objects.count())

            # Check that the log message is correct
            log_entry = LogEntry.objects.all()[0]
            message = '[{"added": {}}]'
            self.assertEqual(message, log_entry.change_message)

            # Check the action flag is set correctly
            self.assertEqual(ADDITION, log_entry.action_flag)

    def test_log_for_create_api_page(self):
        """
        Test that when a page is created via the create page api a log entry is NOT created.
        May help determine why other tests might fail if the api started creating a log for page creation!!
        """

        # Create  a page
        page_data = create_page('home', 'nav_playground.html', 'en', published=True)

        # Check to see if any logs exist, none should exist
        self.assertEqual(0, LogEntry.objects.count())

    def test_log_for_change_admin_page(self):
        """
        Test that a page edit is logged
        """

        superuser = self.get_superuser()

        with self.login_user_context(superuser):

            page_data = self.get_new_page_data()
            response = self.client.post(URL_CMS_PAGE_ADD, page_data)
            page = Page.objects.get(title_set__slug=page_data['slug'], publisher_is_draft=True)

            # Empty any logs
            LogEntry.objects.all().delete()

            # Get and edit the page
            response = self.client.get(URL_CMS_PAGE_CHANGE % page.id)
            page_data['title'] = 'changed title'
            response = self.client.post(URL_CMS_PAGE_CHANGE % page.id, page_data)

            # Test that the log count is correct
            self.assertEqual(1, LogEntry.objects.count())

            # Check that the contents of the log is correct
            log_entry = LogEntry.objects.all()[0]
            message = '[{"changed": {"fields": ["title"]}}]'
            self.assertEqual(message, log_entry.change_message)

            # Check the action flag is set correctly
            self.assertEqual(CHANGE, log_entry.action_flag)

    def test_log_for_move_admin_page(self):
        """

        """

        superuser = self.get_superuser()

        with self.login_user_context(superuser):

            page_home = create_page("page_home", "nav_playground.html", "en", published=False)
            page_1 = create_page("page_a", "nav_playground.html", "en", published=False)
            page_2 = create_page("page_b", "nav_playground.html", "en", published=False)

            # move pages
            response = self.client.post(URL_CMS_PAGE_MOVE % page_2.pk, {"target": page_1.pk, "position": "0"})

            # Test that the log count is correct
            self.assertEqual(1, LogEntry.objects.count())

            # Check that the contents of the log is correct
            log_entry = LogEntry.objects.all()[0]
            message = '[{"moved": {}}]'
            self.assertEqual(message, log_entry.change_message)

            # Check the action flag is set correctly
            self.assertEqual(CHANGE, log_entry.action_flag)


    def test_log_for_delete_admin_page(self):
        """

        """

        superuser = self.get_superuser()

        with self.login_user_context(superuser):

            page = create_page("page_a", "nav_playground.html", "en", published=False)
            endpoint = self.get_admin_url(Page, 'delete', page.pk)
            post_data = {'post': 'yes'}

            response = self.client.post(endpoint, post_data)

            # Test that the log count is correct
            self.assertEqual(1, LogEntry.objects.count())

            # Check that the contents of the log is correct
            log_entry = LogEntry.objects.all()[0]
            message = ""
            self.assertEqual(message, log_entry.change_message)

            # Check the action flag is set correctly
            self.assertEqual(DELETION, log_entry.action_flag)

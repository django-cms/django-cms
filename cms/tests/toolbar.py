from __future__ import with_statement
import re
from django.template.defaultfilters import truncatewords
import datetime

from django.template.defaultfilters import truncatewords
from cms.views import details
import re
from cms.api import create_page, create_title
from cms.cms_toolbar import ADMIN_MENU_IDENTIFIER, ADMINISTRATION_BREAK
from cms.toolbar.items import ToolbarAPIMixin, LinkItem, ItemSearchResult, Break, SubMenu
from cms.toolbar.toolbar import CMSToolbar
from cms.middleware.toolbar import ToolbarMiddleware
from cms.test_utils.testcases import SettingsOverrideTestCase
from cms.test_utils.util.context_managers import SettingsOverride
from django.contrib.auth.models import AnonymousUser, User, Permission
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils.functional import lazy
from django.core.urlresolvers import reverse
from cms.test_utils.project.placeholderapp.models import (Example1, MultilingualExample1)
from cms.test_utils.project.placeholderapp.views import detail_view, detail_view_multi


class ToolbarTestBase(SettingsOverrideTestCase):
    def get_page_request(self, page, user, path=None, edit=False, lang_code='en'):
        path = path or page and page.get_absolute_url()
        if edit:
            path += '?edit'
        request = RequestFactory().get(path)
        request.session = {}
        request.user = user
        request.LANGUAGE_CODE = lang_code
        if edit:
            request.GET = {'edit': None}
        else:
            request.GET = {'edit_off': None}
        request.current_page = page
        mid = ToolbarMiddleware()
        mid.process_request(request)
        request.toolbar.populate()
        return request

    def get_anon(self):
        return AnonymousUser()

    def get_staff(self):
        staff = User(
            username='staff',
            email='staff@staff.org',
            is_active=True,
            is_staff=True,
        )
        staff.set_password('staff')
        staff.save()
        staff.user_permissions.add(Permission.objects.get(codename='change_page'))
        return staff

    def get_nonstaff(self):
        nonstaff = User(
            username='nonstaff',
            email='nonstaff@staff.org',
            is_active=True,
            is_staff=False,
        )
        nonstaff.set_password('nonstaff')
        nonstaff.save()
        nonstaff.user_permissions.add(Permission.objects.get(codename='change_page'))
        return nonstaff

    def get_superuser(self):
        superuser = User(
            username='superuser',
            email='superuser@superuser.org',
            is_active=True,
            is_staff=True,
            is_superuser=True,
        )
        superuser.set_password('superuser')
        superuser.save()
        return superuser


class ToolbarTests(ToolbarTestBase):
    settings_overrides = {'CMS_PERMISSION': False}

    def test_no_page_anon(self):
        request = self.get_page_request(None, self.get_anon(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 0)

    def test_no_page_staff(self):
        request = self.get_page_request(None, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + admin-menu + logout
        self.assertEqual(len(items), 2, items)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 6, admin_items)

    def test_no_page_superuser(self):
        request = self.get_page_request(None, self.get_superuser(), '/')
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + admin-menu + logout
        self.assertEqual(len(items), 2)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 7, admin_items)

    def test_anon(self):
        page = create_page('test', 'nav_playground.html', 'en')
        request = self.get_page_request(page, self.get_anon())
        toolbar = CMSToolbar(request)

        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 0)

    def test_nonstaff(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_nonstaff())
        toolbar = CMSToolbar(request)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + logout
        self.assertEqual(len(items), 0)

    def test_template_change_permission(self):
        with SettingsOverride(CMS_PERMISSIONS=True):
            page = create_page('test', 'nav_playground.html', 'en', published=True)
            request = self.get_page_request(page, self.get_nonstaff())
            toolbar = CMSToolbar(request)
            items = toolbar.get_left_items() + toolbar.get_right_items()
            self.assertEqual([item for item in items if item.css_class_suffix == 'templates'], [])

    def test_markup(self):
        create_page("toolbar-page", "nav_playground.html", "en", published=True)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get('/en/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'nav_playground.html')
        self.assertContains(response, '<div id="cms_toolbar"')
        self.assertContains(response, 'cms.base.css')

    def test_markup_generic_module(self):
        create_page("toolbar-page", "col_two.html", "en", published=True)
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get('/en/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, '<div class="cms_submenu-item cms_submenu-item-title"><span>Generic</span>')

    def test_markup_flash_custom_module(self):
        superuser = self.get_superuser()
        create_page("toolbar-page", "col_two.html", "en", published=True)
        with self.login_user_context(superuser):
            response = self.client.get('/en/?edit')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'href="LinkPlugin">')
        self.assertContains(response,
                            '<div class="cms_submenu-item cms_submenu-item-title"><span>Different Grouper</span>')

    def test_show_toolbar_to_staff(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_with_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, AnonymousUser(), edit=True)
        toolbar = CMSToolbar(request)
        self.assertTrue(toolbar.show_toolbar)

    def test_show_toolbar_without_edit(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, AnonymousUser(), edit=False)
        toolbar = CMSToolbar(request)
        self.assertFalse(toolbar.show_toolbar)

    def test_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_superuser(), edit=True)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        self.assertEqual(len(items), 7)

    def test_no_publish_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        request = self.get_page_request(page, self.get_staff(), edit=True)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertTrue(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))
        self.assertTrue(toolbar.edit_mode)
        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + edit-mode + templates + page-menu + admin-menu + logout
        self.assertEqual(len(items), 6)

    def test_no_change_button(self):
        page = create_page('test', 'nav_playground.html', 'en', published=True)
        user = self.get_staff()
        user.user_permissions.all().delete()
        request = self.get_page_request(page, user, edit=True)
        toolbar = CMSToolbar(request)
        toolbar.populate()
        toolbar.post_template_populate()
        self.assertFalse(page.has_change_permission(request))
        self.assertFalse(page.has_publish_permission(request))

        items = toolbar.get_left_items() + toolbar.get_right_items()
        # Logo + page-menu + admin-menu + logout
        self.assertEqual(len(items), 3, items)
        admin_items = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'Test').get_items()
        self.assertEqual(len(admin_items), 6, admin_items)

    def test_button_consistency_staff(self):
        """
        Tests that the buttons remain even when the language changes.
        """
        user = self.get_staff()
        cms_page = create_page('test-en', 'nav_playground.html', 'en', published=True)
        create_title('de', 'test-de', cms_page)
        cms_page.publish('de')
        en_request = self.get_page_request(cms_page, user, edit=True)
        en_toolbar = CMSToolbar(en_request)
        en_toolbar.populate()
        en_toolbar.post_template_populate()
        self.assertEqual(len(en_toolbar.get_left_items() + en_toolbar.get_right_items()), 6)
        de_request = self.get_page_request(cms_page, user, path='/de/', edit=True, lang_code='de')
        de_toolbar = CMSToolbar(de_request)
        de_toolbar.populate()
        de_toolbar.post_template_populate()
        self.assertEqual(len(de_toolbar.get_left_items() + de_toolbar.get_right_items()), 6)

    def test_placeholder_name(self):
        with SettingsOverride(CMS_PLACEHOLDER_CONF={
            'col_left': {'name': 'PPPP'}
        }):
            superuser = self.get_superuser()
            create_page("toolbar-page", "col_two.html", "en", published=True)
            with self.login_user_context(superuser):
                response = self.client.get('/en/?edit')
            self.assertEquals(response.status_code, 200)
            self.assertContains(response, 'PPPP')

    def test_user_settings(self):
        superuser = self.get_superuser()
        with self.login_user_context(superuser):
            response = self.client.get('/en/admin/cms/usersettings/')
            self.assertEqual(response.status_code, 200)

    def test_get_alphabetical_insert_position(self):
        page = create_page("toolbar-page", "nav_playground.html", "en",
                           published=True)
        request = self.get_page_request(page, self.get_staff(), '/')
        toolbar = CMSToolbar(request)
        toolbar.get_left_items()
        toolbar.get_right_items()

        admin_menu = toolbar.get_or_create_menu(ADMIN_MENU_IDENTIFIER, 'TestAppMenu')

        # Insert alpha
        alpha_position = admin_menu.get_alphabetical_insert_position('menu-alpha', SubMenu, None)

        # As this will be the first item added to this, this use should return the default, or namely None
        if not alpha_position:
            alpha_position = admin_menu.find_first(Break, identifier=ADMINISTRATION_BREAK) + 1
        menu = admin_menu.get_or_create_menu('menu-alpha', 'menu-alpha', position=alpha_position)

        # Insert gamma (should return alpha_position + 1)
        gamma_position = admin_menu.get_alphabetical_insert_position('menu-gamma', SubMenu)
        self.assertEquals(int(gamma_position), int(alpha_position) + 1)
        admin_menu.get_or_create_menu('menu-gamma', 'menu-gamma', position=gamma_position)

        # Where should beta go? It should go right where gamma is now...
        beta_position = admin_menu.get_alphabetical_insert_position('menu-beta', SubMenu)
        self.assertEqual(beta_position, gamma_position)


class EditModelTemplateTagTest(ToolbarTestBase):
    urls = 'cms.test_utils.project.placeholderapp_urls'
    edit_fields_rx = "(\?|&amp;)edit_fields=%s"

    def tearDown(self):
        Example1.objects.all().delete()
        MultilingualExample1.objects.all().delete()
        super(EditModelTemplateTagTest, self).tearDown()

    def test_anon(self):
        user = self.get_anon()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, "<h1>char_1</h1>")
        self.assertNotContains(response, "CMS.API")

    def test_noedit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, "<h1>char_1</h1>")
        self.assertContains(response, "CMS.API")

    def test_edit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'char_1', ex1.pk))

    def test_invalid_item(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model fake "char_1" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<div class="cms_plugin cms_plugin-%s"></div>' % ex1.pk)

    def test_as_varname(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" as tempvar %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertNotContains(response, '<div class="cms_plugin cms_plugin-%s"></div>' % ex1.pk)

    def test_filters(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2' %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">%s</div></h1>' % (
        'placeholderapp', 'example1', 'char_1', ex1.pk, truncatewords(ex1.char_1, 2)))

    def test_filters_date(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4", date_field=datetime.date(2012, 1, 1))
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)

        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">%s</div></h1>' % (
        'placeholderapp', 'example1', 'date_field', ex1.pk, ex1.date_field.strftime("%Y-%m-%d")))

        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "date_field" "" "" 'date:"Y m d"' %}</h1>
{% endblock content %}
'''
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">%s</div></h1>' % (
        'placeholderapp', 'example1', 'date_field', ex1.pk, ex1.date_field.strftime("%Y %m %d")))

    def test_filters_notoolbar(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1, <p>hello</p>, <p>hello</p>, <p>hello</p>, <p>hello</p>", char_2="char_2",
                       char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "char_1" "" "" 'truncatewords:2'  %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=False)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1>%s</h1>' % truncatewords(ex1.char_1, 2))

    def test_no_cms(self):
        user = self.get_staff()
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance %}
{% endblock content %}
'''
        request = self.get_page_request('', user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<div class="cms_plugin cms_plugin-%s-%s-%s cms_render_model_icon"><img src="/static/cms/img/toolbar/render_model_placeholder.png"></div>' % (
                            'placeholderapp', 'example1', ex1.pk))
        self.assertContains(response, '\'redirectOnClose\': false,')

    def test_icon_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_icon instance %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<div class="cms_plugin cms_plugin-%s-%s-%s cms_render_model_icon"><img src="/static/cms/img/toolbar/render_model_placeholder.png"></div>' % (
                            'placeholderapp', 'example1', ex1.pk))

    def test_add_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
{% render_model_add instance %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response,
                            '<div class="cms_plugin cms_plugin-%s-%s-add-%s cms_render_model_add"><img src="/static/cms/img/toolbar/render_model_placeholder.png"></div>' % (
                            'placeholderapp', 'example1', ex1.pk))

    def test_block_tag(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4", date_field=datetime.date(2012, 1, 1))
        ex1.save()

        # This template does not render anything as content is saved in a
        # variable and never inserted in the page
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}{% load url from future %}

{% block content %}
{% render_model_block instance as rendered_model %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    {{ instance.date_field|date:"Y" }}
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertNotContains(response,
                               '<div class="cms_plugin cms_plugin-%s-%s-%s cms_render_model_icon"><img src="/static/cms/img/toolbar/render_model_icon.png"></div>' % (
                               'placeholderapp', 'example1', ex1.pk))

        # This template does not render anything as content is saved in a
        # variable and inserted in the page afterwards
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}{% load url from future %}

{% block content %}
{% render_model_block instance as rendered_model %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    <span class="date">{{ instance.date_field|date:"Y" }}</span>
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{{ rendered_model }}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(response,
                            '<div class="cms_plugin cms_plugin-%s-%s-%s">' % ('placeholderapp', 'example1', ex1.pk))
        self.assertContains(response, '<h1>%s - %s</h1>' % (ex1.char_1, ex1.char_2))
        self.assertContains(response, '<span class="date">%s</span>' % (ex1.date_field.strftime("%Y")))
        self.assertContains(response, '<a href="%s">successful if</a></div>' % (reverse('detail', args=(ex1.pk,))))

        # This template is rendered directly
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}{% load url from future %}

{% block content %}
{% render_model_block instance %}
    {{ instance }}
    <h1>{{ instance.char_1 }} - {{  instance.char_2 }}</h1>
    <span class="date">{{ instance.date_field|date:"Y" }}</span>
    {% if instance.char_1 %}
    <a href="{% url 'detail' instance.pk %}">successful if</a>
    {% endif %}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(response,
                            '<div class="cms_plugin cms_plugin-%s-%s-%s">' % ('placeholderapp', 'example1', ex1.pk))
        self.assertContains(response, '<h1>%s - %s</h1>' % (ex1.char_1, ex1.char_2))
        self.assertContains(response, '<span class="date">%s</span>' % (ex1.date_field.strftime("%Y")))
        self.assertContains(response, '<a href="%s">successful if</a></div>' % (reverse('detail', args=(ex1.pk,))))

        # Changelist check
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}{% load url from future %}

{% block content %}
{% render_model_block instance 'changelist' %}
    {{ instance }}
{% endrender_model_block %}
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        # Assertions on the content of the block tag
        self.assertContains(response, '<div class="cms_plugin cms_plugin-%s-%s-changelist-%s">' % ('placeholderapp', 'example1', ex1.pk))

    def test_invalid_attribute(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "fake_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<div class="cms_plugin cms_plugin-%s-%s-%s-%s"></div>' % (
        'placeholderapp', 'example1', 'fake_field', ex1.pk))

        # no attribute
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}CIAOOOO
<h1>{% render_model instance "" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<div class="cms_plugin cms_plugin-%s"></div>' % ex1.pk)

    def test_callable_item(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_view_method(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "" "dynamic_url" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_method_attribute(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "" "static_admin_url" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        ex1.set_static_url(request)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_admin_url(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_admin_url_extra_field(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_2" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))
        self.assertContains(response, "/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_2", response.content.decode('utf8')))

    def test_admin_url_multiple_fields(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" "char_1,char_2" "en" "" "admin:placeholderapp_example1_edit_field" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))
        self.assertContains(response, "/admin/placeholderapp/example1/edit-field/%s/en/" % ex1.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_1", response.content.decode('utf8')))
        self.assertTrue(re.search(self.edit_fields_rx % "char_1%2Cchar_2", response.content.decode('utf8')))

    def test_instance_method(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance "callable_item" %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_item_from_context(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()
        template_text = '''{% extends "base.html" %}
{% load cms_tags %}

{% block content %}
<h1>{% render_model instance item_name %}</h1>
{% endblock content %}
'''
        request = self.get_page_request(page, user, edit=True)
        response = detail_view(request, ex1.pk, template_string=template_text,
                               item_name="callable_item")
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">char_1</div></h1>' % (
        'placeholderapp', 'example1', 'callable_item', ex1.pk))

    def test_edit_field(self):
        from django.contrib.admin import site

        exadmin = site._registry[Example1]

        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        request = self.get_page_request(page, user, edit=True)
        request.GET['edit_fields'] = 'char_1'
        response = exadmin.edit_field(request, ex1.pk, "en")
        self.assertContains(response, 'id="id_char_1"')
        self.assertContains(response, 'value="char_1"')

    def test_edit_field_not_allowed(self):
        from django.contrib.admin import site

        exadmin = site._registry[Example1]

        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        ex1 = Example1(char_1="char_1", char_2="char_2", char_3="char_3",
                       char_4="char_4")
        ex1.save()

        request = self.get_page_request(page, user, edit=True)
        request.GET['edit_fields'] = 'char_3'
        response = exadmin.edit_field(request, ex1.pk, "en")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content.decode('utf8'), 'Fields char_3 not editabled in the frontend')

    def test_multi_edit(self):
        user = self.get_staff()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        title = create_title("fr", "test", page)

        exm = MultilingualExample1()
        exm.translate("en")
        exm.char_1 = 'one'
        exm.char_2 = 'two'
        exm.save()
        exm.translate("fr")
        exm.char_1 = "un"
        exm.char_2 = "deux"
        exm.save()

        request = self.get_page_request(page, user, edit=True)
        response = detail_view_multi(request, exm.pk)
        self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">one</div></h1>' % (
        'placeholderapp', 'multilingualexample1', 'char_1', exm.pk))
        self.assertContains(response, "/admin/placeholderapp/multilingualexample1/edit-field/%s/en/" % exm.pk)
        self.assertTrue(re.search(self.edit_fields_rx % "char_1", response.content.decode('utf8')))
        self.assertTrue(re.search(self.edit_fields_rx % "char_1%2Cchar_2", response.content.decode('utf8')))

        with SettingsOverride(LANGUAGE_CODE="fr"):
            request = self.get_page_request(title.page, user, edit=True, lang_code="fr")
            response = detail_view_multi(request, exm.pk)
            self.assertContains(response, '<h1><div class="cms_plugin cms_plugin-%s-%s-%s-%s">un</div></h1>' % (
            'placeholderapp', 'multilingualexample1', 'char_1', exm.pk))
            self.assertContains(response, "/admin/placeholderapp/multilingualexample1/edit-field/%s/fr/" % exm.pk)
            self.assertTrue(re.search(self.edit_fields_rx % "char_1%2Cchar_2", response.content.decode('utf8')))

    def test_edit_field_multilingual(self):
        from django.contrib.admin import site

        exadmin = site._registry[MultilingualExample1]

        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', 'en', published=True)
        title = create_title("fr", "test", page)

        exm = MultilingualExample1()
        exm.translate("en")
        exm.char_1 = 'one'
        exm.char_2 = 'two'
        exm.save()
        exm.translate("fr")
        exm.char_1 = "un"
        exm.char_2 = "deux"
        exm.save()

        request = self.get_page_request(page, user, edit=True)
        request.GET['edit_fields'] = 'char_2'

        response = exadmin.edit_field(request, exm.pk, "en")
        self.assertContains(response, 'id="id_char_2"')
        self.assertContains(response, 'value="two"')

        response = exadmin.edit_field(request, exm.pk, "fr")
        self.assertContains(response, 'id="id_char_2"')
        self.assertContains(response, 'value="deux"')

        with SettingsOverride(LANGUAGE_CODE="fr"):
            request = self.get_page_request(title.page, user, edit=True, lang_code="fr")
            request.GET['edit_fields'] = 'char_2'
            response = exadmin.edit_field(request, exm.pk, "fr")
            self.assertContains(response, 'id="id_char_2"')
            self.assertContains(response, 'value="deux"')

    def test_edit_page(self):
        language = "en"
        user = self.get_superuser()
        page = create_page('Test', 'col_two.html', language, published=True)
        title = page.get_title_obj(language)
        title.menu_title = 'Menu Test'
        title.page_title = 'Page Test'
        title.title = 'Main Test'
        title.save()
        page.publish('en')
        page.reload()
        request = self.get_page_request(page, user, edit=True)
        response = details(request, '')
        self.assertContains(response, '<div class="cms_plugin cms_plugin-cms-page-get_page_title-%s">%s</div>' % (
        page.pk, page.get_page_title(language)))
        self.assertContains(response, '<div class="cms_plugin cms_plugin-cms-page-get_menu_title-%s">%s</div>' % (
        page.pk, page.get_menu_title(language)))
        self.assertContains(response, '<div class="cms_plugin cms_plugin-cms-page-get_title-%s">%s</div>' % (page.pk, page.get_title(language)))
        self.assertContains(response, '<div class="cms_plugin cms_plugin-cms-page-changelist-%s"><h3>Menu</h3></div>' % page.pk)


class ToolbarAPITests(TestCase):
    def test_find_item(self):
        api = ToolbarAPIMixin()
        first = api.add_link_item('First', 'http://www.example.org')
        second = api.add_link_item('Second', 'http://www.example.org')
        all_links = api.find_items(LinkItem)
        self.assertEqual(len(all_links), 2)
        result = api.find_first(LinkItem, name='First')
        self.assertNotEqual(result, None)
        self.assertEqual(result.index, 0)
        self.assertEqual(result.item, first)
        result = api.find_first(LinkItem, name='Second')
        self.assertNotEqual(result, None)
        self.assertEqual(result.index, 1)
        self.assertEqual(result.item, second)
        no_result = api.find_first(LinkItem, name='Third')
        self.assertEqual(no_result, None)

    def test_find_item_lazy(self):
        lazy_attribute = lazy(lambda x: x, str)('Test')
        api = ToolbarAPIMixin()
        api.add_link_item(lazy_attribute, None)
        result = api.find_first(LinkItem, name='Test')
        self.assertNotEqual(result, None)
        self.assertEqual(result.index, 0)

    def test_not_is_staff(self):
        request = RequestFactory().get('/en/?edit')
        request.session = {}
        request.LANGUAGE_CODE = 'en'
        request.user = AnonymousUser()
        toolbar = CMSToolbar(request)
        self.assertEqual(len(toolbar.get_left_items()), 0)
        self.assertEqual(len(toolbar.get_right_items()), 0)

    def test_item_search_result(self):
        item = object()
        result = ItemSearchResult(item, 2)
        self.assertEqual(result.item, item)
        self.assertEqual(int(result), 2)
        result += 2
        self.assertEqual(result.item, item)
        self.assertEqual(result.index, 4)

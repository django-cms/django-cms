# -*- coding: utf-8 -*-
from cms.api import add_plugin
from cms.test_utils.project.fakemlng.models import MainModel, Translations


class FakemlngFixtures(object):
    def create_fixtures(self):
        main = MainModel.objects.create()
        en = Translations.objects.create(master=main, language_code='en')
        Translations.objects.create(master=main, language_code='de')
        Translations.objects.create(master=main, language_code='nl')
        fr = Translations.objects.create(master=main, language_code='fr')
        add_plugin(en.placeholder, 'TextPlugin', 'en', body='<p>ENGLISH</p>')
        add_plugin(fr.placeholder, 'TextPlugin', 'fr', body='<p>FRENCH</p>')

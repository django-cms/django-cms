# -*- coding: utf-8 -*-
import os
from django.test import TestCase
from django.core.management import call_command

from cms.models.pagemodel import Page


class FixtureTestCase(TestCase):

    #fixtures = ['cms.json',]
    def setUp(self):
        pass

    def test_fixture_load(self):
        self.assertEqual(0, Page.objects.count())
        call_command('loaddata', 'cms.json')
        self.assertEqual(3, Page.objects.count())

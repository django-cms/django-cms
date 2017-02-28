# -*- coding: utf-8 -*-
from cms.models import CMSPlugin


class TestPlugin1(CMSPlugin):
    pass


class LeftMixin(object): pass

class RightMixin(object): pass


class TestPlugin2(LeftMixin, CMSPlugin, RightMixin):
    pass

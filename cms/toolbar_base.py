# -*- coding: utf-8 -*-


class CMSToolbar(object):
    def __init__(self, request, toolbar, is_current_app, app_path):
        self.request = request
        self.toolbar = toolbar
        self.is_current_app = is_current_app
        self.app_path = app_path

    def populate(self):
        raise NotImplemented('populate() is not implemented')

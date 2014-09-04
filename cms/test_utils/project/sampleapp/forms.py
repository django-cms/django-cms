# -*- coding: utf-8 -*-
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    pass


class LoginForm2(AuthenticationForm):
    pass


class LoginForm3(AuthenticationForm):
    def __init__(self, argument, request=None, *args, **kwargs):
        super(LoginForm3, self).__init__(request, *args, **kwargs)

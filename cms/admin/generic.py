# -*- coding: utf-8 -*-
import inspect
from django.contrib import admin


class CallableDisplayWithRequest(object):
    """
    Allows "function" in list_display to be call with request and have a correct representation 
    when casting to str : avoid having this type of generated HTML for exemple:
        <td class="field-&lt;function test as 0x7f9beaa31b18&gt;">
    """
    
    def __init__(self, to_call, request, str_repr=None):
        self.__to_call = to_call
        self.__request = request
        if str_repr is None:
            if hasattr(to_call, '__name__'):
                self.__str_repr = to_call.__name__
            else:
                self.__str_repr = to_call.__repr__()
        else:
            self.__str_repr = str_repr

    def __getattribute__(self, name):
        if name[0:27] == ('_CallableDisplayWithRequest'):
            return super(CallableDisplayWithRequest, self).__getattribute__(name)
        else:
            return self.__to_call.__getattribute__(name)

    def __repr__(self):
        return self.__str_repr

    def __call__(self, *args, **kwargs):
        kwargs['request'] = self.__request
        return self.__to_call(*args, **kwargs)


class AddRequestToListdisplayAdminMixin(object):
    """
    This mixin add request argument to collables used in
    list_display list. This is a kind of django workarround.

    If the callable has a "request" arg, we replace the callable with an instance of
    `CallableDisplayWithRequest` which will call the initial callable with a request kwarg added.
    """

    def get_list_display(self, request):
        list_display = super(AddRequestToListdisplayAdminMixin, self).get_list_display(request)

        for name in list_display:
            if callable(name):
                attr = name
            elif hasattr(self, name) and name not in ('__str__', '__unicode__'):
                attr = getattr(self, name)
                if not callable(attr):
                    continue
            else:
                continue

            (args, varargs, keywords, defaults) = inspect.getargspec(attr)

            if 'request' in args:
                index = list_display.index(name)
                list_display[index] = CallableDisplayWithRequest(attr, request)

        return list_display


class GenericAdmin(admin.ModelAdmin):
    change_list_template = 'admin/cms/custom_models/change_list.html'


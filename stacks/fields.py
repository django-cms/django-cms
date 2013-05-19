# -*- coding: utf-8 -*-
from django_select2.fields import AutoModelSelect2Field
from stacks.models import Stack


class StackSearchField(AutoModelSelect2Field):
    search_fields = ('name__icontains', 'code__icontains',)
    queryset = Stack.objects

    def security_check(self, request, *args, **kwargs):
        user = request.user
        if user and not user.is_anonymous() and user.is_staff and user.has_perm('djangocms_stack.change_stack'):
            return True
        return False

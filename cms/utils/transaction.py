# -*- coding: utf-8 -*-


def wrap_transaction(*args, **kwargs):
    from django.db import transaction
    try:
        transaction.atomic
        return transaction.atomic(*args, **kwargs)
    except:
        return transaction.commit_on_success(*args, **kwargs)
# -*- coding: utf-8 -*-
def wrap_transaction(*args, **kwargs):
    """
    This is a simple  decorator that wraps
    transaction.commit_on_success / atomic decorators.

    While the two are not equivalent, they can be regarded as equal for the
    use in the cms codebase.
    """
    from django.db import transaction
    try:
        from django.db.transaction import atomic  # nopyflakes
        return transaction.atomic(*args, **kwargs)
    except ImportError:
        return transaction.commit_on_success(*args, **kwargs)

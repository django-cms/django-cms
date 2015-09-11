# for Django 1.6/Python 2.6
import unittest as stdut


def _skipIf(check, message=''):
    def _deco(meth):
        if check:
            return lambda *a, **kw: None
        else:
            return meth
    return _deco

if hasattr(stdut, 'skipIf'):
    skipIf = stdut.skipIf
else:
    skipIf = _skipIf

from __future__ import with_statement
from spidermonkey import Runtime
import os
import unittest

THISDIR = os.path.abspath(os.path.dirname(__file__))
MEDIADIR = os.path.join(THISDIR, '../media/cms/')

class BaseJavascriptTestCase(unittest.TestCase):
    def _get_runtime(self):
        return Runtime()
    
    def _get_context(self):
        rt = self._get_runtime()
        return rt.new_context()
    
    def _get_file_path(self, *bits):
        return os.path.join(MEDIADIR, *bits)
    
    def _run_javascript(self, files, snippet):
        ctx = self._get_context()
        for filename in files:
            with open(filename, 'r') as fobj:
                lib = fobj.read()
                ctx.execute(lib)
        return ctx.execute(snippet)
'''
Created on Dec 23, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''
import StringIO
import sys


class StdoutOverride(object):
    """
    This overrides Python's the standard output and redirrects it to a StringIO
    object, so that on can test the output of the program.
    
    example:
    lines = None
    with StdoutOverride() as buffer:
        # print stuff
        lines = buffer.getvalue()
    """
    def __enter__(self):
        self.buffer = StringIO.StringIO()
        sys.stdout = self.buffer
        return self.buffer
        
    def __exit__(self, type, value, traceback):
        self.buffer.close()
        # Revert the stdout to the real one
        sys.stdout = sys.__stdout__
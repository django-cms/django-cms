'''
Created on Dec 23, 2010

@author: Christopher Glass <christopher.glass@divio.ch>
'''
import StringIO
import sys


class StandardIOOverride(object):
    """
    
    """
    def __enter__(self):
        buffer = StringIO.StringIO()
        sys.stdout = buffer
        return buffer
        
    def __exit__(self, type, value, traceback):
        # Revert the stdout to the real one
        sys.stdout = sys.__stdout__
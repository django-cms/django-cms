#!/usr/bin/python
'''
Created on Sep 2, 2010

@author: Chris Glass (chirstopher.glass@divio.ch)

FOR ECLIPSE DEBUG ONLY!
'''
from django.core.management import execute_manager

import sys

# The relative path is: ../../bin/django:
imat = sys.argv[0]
filename = imat.replace('tests/testapp/eclipse_manage.py','tests/bin/django')

# This will only work on unix :(
lines = None
with open(filename, 'r') as working_file:
    lines = working_file.readlines()
    
recording = False
egg_paths = []
for line in lines:
    if recording:
        if ']' in line:
            recording = False
        else:
            egg_path = line.replace('\'','').replace(',','').replace(' ','').replace('\n','')
            egg_paths.append(egg_path)
    else:
        if 'sys.path[0:0] = [' in line:
            recording = True
            
sys.path[0:0] = egg_paths

try:
    import settings as setting_file # Assumes it's located in settings/
except ImportError:
    import sys
    sys.stderr.write("Could not find settings file")
    sys.exit(1)

if __name__ == "__main__":
    execute_manager(setting_file)
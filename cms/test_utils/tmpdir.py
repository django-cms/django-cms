# -*- coding: utf-8 -*-
from contextlib import contextmanager
from tempfile import mkdtemp
import os
import random
import shutil
import stat


@contextmanager
def temp_dir():
    name = make_temp_dir()
    yield name
    shutil.rmtree(name)

def make_temp_dir():
    if os.path.exists('/dev/shm/'):
        if os.stat('/dev/shm').st_mode & stat.S_IWGRP:
            dirname = 'django-cms-tests-%s' % random.randint(1,1000000)
            path = os.path.join('/dev/shm', dirname)
            while os.path.exists(path):
                dirname = 'django-cms-tests-%s' % random.randint(1,1000000)
                path = os.path.join('/dev/shm', dirname)
                os.mkdir(path)
                return path
    return mkdtemp()

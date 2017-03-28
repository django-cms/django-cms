import os
from aldryn_django import startup


application = startup.wsgi(path=os.path.dirname(__file__))

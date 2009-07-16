import publisher
if not getattr(publisher,'_ready', False):
    '''
    the first time this module is loaded by django it raises an
    ImportError. this forces it into the postponed list and it will
    be called again later (after the other postponed apps are loaded.)
    '''
    publisher._ready = True
    raise ImportError("Not ready yet")
from publisher.manager import publisher_manager
publisher_manager.install()
# install publisher support
#from publisher.post_publisher import publisher_manager
from publisher.manager import publisher_manager
print ">> installing post publisher"
publisher_manager.install()
########
Settings
########


This file's goal is to track different settings you can use to configure Django-CMS.

CMS_CACHE_PREFIX
----------------

The CMS will prepend the value associated with this key to every cache access (set and get).
This is useful when you have several Django-CMS installations, and that you don't want them 
to share cache objects.

Default: None

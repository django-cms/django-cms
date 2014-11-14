.. _common_issues:

#############
Common issues
#############

**********************************************
Caught MultipleObjectsReturned while rendering
**********************************************

After upgrading to a new version with an existing database, you encounter 
something like:

Caught MultipleObjectsReturned while rendering: get() returned more than 
one CacheKey -- it returned 12! Lookup parameters were {'key': 
'cms-menu_nodes_en_1_1_user', 'language': 'en', 'site': 1L}

What has happened is that your database contains some old cache data in 
the `menus_cachekey` table. Just delete all those entries.

*****************************************
Sandbox access violation: Blocked a frame
*****************************************

Setting an x-frame-options header with DENY value will break certain toolbar 
functionality. This is independent of any `x-frame-options` functionality 
offerred by django CMS.

Example error in browser console (as worded by Chrome):

    Uncaught SecurityError: Failed to read the 'contentDocument' property 
    from 'HTMLIFrameElement': Sandbox access violation: Blocked a frame at 
    "http://0.0.0.0:8000" from accessing a frame at "null".  The frame being 
    accessed is sandboxed and lacks the "allow-same-origin" flag. 
    
Some examples, places that might set a `x-frame-options` header:

* Django security middleware like ``django.middleware.clickjacking.XFrameOptionsMiddleware``
* Third-party apps like ``djangosecure``
* Your server (Apache, Nginx, etc.) or cloud provider
* Client-side browswer plugins with clickjacking protection

If you set a `x-frame-options` header independently from DjangoCMS, because the value 
is `SAMEORIGIN` or allow frames from certain URIs `ALLOW-FROM uri`. For more information, 
please read X-Frame-Options article on Mozilla Developer Network:

https://developer.mozilla.org/en-US/docs/Web/HTTP/X-Frame-Options

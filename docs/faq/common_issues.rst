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

Setting an `x-frame-options` header will break certain toolbar funcationality.

For example, `djangosecure` will set the header `x-frame-options: DENY` for you.

Example error in browser console:

    Uncaught SecurityError: Failed to read the 'contentDocument' property 
    from 'HTMLIFrameElement': Sandbox access violation: Blocked a frame at 
    "http://0.0.0.0:8000" from accessing a frame at "null".  The frame being 
    accessed is sandboxed and lacks the "allow-same-origin" flag. 

Ensure you are sending no `x-frame-options` header or set it to 
`SAMEORIGIN` or certain URIs `ALLOW-FROM uri`.

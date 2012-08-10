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


.. _frontend_admin:

##################################
Working with admin in the frontend
##################################

By clicking on the **Administration** item in the site menu, a left sideframe opens
on the current website Django admin.
This allows any kind of interaction with the "traditional" Django admin.


************
Redirections
************

When an object is created or edited while the user is on the website frontend,
a redirection occurs to redirect the user to the current address of the created
/ edited instance.

Redirections follow rules below:

* Anonymous user (for example during logoff) is always redirected to the
  home page;
* When a model instance has changed (see :ref:`url_changes`) the frontend
  is redirected to the instance URL; in case of django CMS pages, the publishing
  state is taken into account: if the toolbar is in *Draft* mode the user is
  redirected to the *draft* page URL, if in *Live* mode, the user is redirected
  to the page if is published, otherwise it's switched in *Draft* mode and redirected
  to the *draft* page URL;
* If the edited object or its URL can't be retrieved, no redirection occurs;

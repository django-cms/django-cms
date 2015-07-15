.. _frontend_admin:

##################################
Working with admin in the frontend
##################################

The *Administration...* item in the :ref:`site-menu`, opens the :ref:`side-frame <side-frame>`
containing the site's Django admin. This allows the usual interaction with the "traditional" Django
admin.

***********
Redirection
***********

When an object is created or edited while the user is on the website frontend, a redirection occurs
to redirect the user to the current address of the created/edited instance.

This redirection follows the rules below:

* an anonymous user (for example, after logging out) is always redirected to the home page
* when a model instance has changed (see :ref:`url_changes`) the frontend is redirected to the
  instance URL, and:

  * in case of django CMS pages, the publishing state is taken into account, and then

    * if the toolbar is in *Draft* mode the user is redirected to the *draft* page URL
    * if in *Live* mode:

      * the user is redirected to the page if is published
      * otherwise it's switched in *Draft* mode and redirected to the *draft* page URL

* if the edited object or its URL can't be retrieved, no redirection occurs

Yes, it's complex - but there is a logic to it, and it's actually easier to understand when you're
using it than by reading about it, so don't worry too much. The point is that django CMS always
tries to redirect you to the most sensible place when it has to.

######
Log in
######

On a brand new site, you will see the default django CMS page:

.. figure:: /images/initial-page.png
   :figwidth: 300
   :align: right

The first step is to log into your site. You will need login credentials which
are typically a username or email address plus a password. The developers of
your site are responsible for creating and providing these credentials to you
so consult them if you are unsure.

Your site will likely have a dedicated login page but a quick way to trigger
the login form from any page is to simply append ``?edit`` to the url.
Alternatively, hit *Switch to edit mode* on the default page).

This will reveal the :ref:`django CMS toolbar <toolbar>`, with a login prompt
if you're not already logged-in:

.. figure:: /images/login-form.png

And once you are logged in, the toolbar will display some key editing tools:

.. figure:: /images/logged-in.png

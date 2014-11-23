##############
Editing Basics
##############

This guide focuses on the basics of content creation and editing using django
CMS's powerful front-end editing mode. This guide is suitable for non-technical
and technical audiences alike.

This guide can only cover the basics that are common to most sites built using
django CMS. Your own site will likely have many customisations and special
purpose plugins which we cannot cover here. Nevertheless, by the end of this
guide you should be comfortable with the content editing process using django
CMS. Many of the skills you'll learn will be transferable to any custom plugins
your site may have.

***************
Getting Started
***************

On a brand new site, you will see the default django CMS page:

.. figure:: /images/initial-page.png
   :figwidth: 300
   :align: right


Log in
======

The first step is to log into your site. You will need login credentials which
are typically a username or email address plus a password. The developers of
your site are responsible for creating and providing these credentials to you
so consult them if you are unsure.

Your site will likely have a dedicated login page but a quick way to trigger
the login form from any page is to simply append ``?edit`` to the url.
Alternatively, hit 'Switch to edit mode' on the default page).

This will reveal the toolbar, with a login prompt if you're not already
logged-in:

.. figure:: /images/login-form.png

And once you are logged in, the toolbar will display some key editing tools:

.. figure:: /images/logged-in.png

Add a page
==========

Select the *Pages...* menu item from the *Site menu* (*example.com* in the
example below, though yours may have a different name) in the toolbar.

.. figure:: /images/pages-menu-item.png
   :figwidth: 300
   :align: right

This reveals the *side-frame* for page administration.

.. figure:: /images/no-pages.png

Hit **Add page**.

.. figure:: /images/page-basic-settings.png
   :figwidth: 300
   :align: right
   :figclass: clearfix

You're now asked for some basic settings for the new page.

Just give it a ``Title`` - call it "Home". You can ignore the rest for now.

You will notice that the ``slug`` is completed automatically, based on the
``Title``.

When you are finished entering these fields, press **Save**. The *page editing
form* is replaced with the *page list*. It's a short list: you only have
one item in it.

.. figure:: /images/my-first-page.png

In the meantime to see the page you've just created, press *Home* in the page
list; it'll be displayed in the main frame:

.. figure:: /images/empty-page.png

Adding content to a page
========================

.. figure:: /images/add-text-plugin.png
   :figwidth: 400
   :align: right
   :figclass: clearfix

Your page is empty of course. We need to add some content to it, by adding a
*plugin*. In the toolbar, you'll notice that we're in *Content* mode. Change
that to *Structure* mode.

This reveals the *placeholders* available on the page

On any placeholder, click the menu icon on the right side to reveal the list of
available plugins. In this case, we'll choose the *Text* plugin. Invoking the
*Text* plugin will open your installed text editor plugin. Enter some text and
press "Save". When you save the plugin, your plugin will now be displayed
"inside" the placeholder as shown in this progression of images:

Previewing a page
=================

To preview the page, switch back to *Content* mode using the button in the
toolbar.

You can continue editing existing plugins in *Content* mode simply by
double-clicking the content they present. Try it: double-click on the text you
have just entered, and the text editor will open again for you to make some
more changes.

To add new plugins, or to re-arrange existing ones, switch back into *Structure*
mode.

Publishing
==========

Your page is a *draft* - only you can see it. To publish it so that ordinary web visitors can see, hit **Publish changes**.

You'll notice that the toolbar indicates you're now seeing a *Live* view of
your page. If you want to make further changes:

* switch back to *Draft* mode
* make further changes in *Structure* or *Content* mode
* **Publish changes** when you're ready

Until you publish your changes, you can continue working on the draft without
affecting the published page.

You have now worked through the complete cycle of content publishing in django
CMS.

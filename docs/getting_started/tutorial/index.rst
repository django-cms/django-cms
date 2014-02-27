*********************
django CMS 3 Tutorial
*********************

You've just setup your CMS, so let's get started using it - that's the best part! Welcome to the django CMS 3 tutorial!

Run your server with ``python manage.py runserver``, then point a web browser to
`127.0.0.1:8000/admin/ <http://127.0.0.1:8000/admin/>`_ , and log in using the super
user credentials you defined earlier.

Once in the admin part of your site, you should see something like the following:

|first-admin|

.. |first-admin| image:: ../../images/first-admin.png


Adding a page
-------------

Adding a page is as simple as clicking "Pages" in the admin view, then the "add page" button
at the top right-hand corner of the screen.

This is where you select which template to use (remember, we created two), as well as
pretty obvious things like which language the page is in (used for internationalisation),
the page's title, and the url slug it will use.

Hitting the "Save" button, unsurprisingly, saves the page. It will now display in the list of
pages.

|my-first-page|

.. |my-first-page| image:: ../../images/my-first-page.png

Congratulations! You now have a fully functional django CMS installation!


Publishing a page
-----------------

The following is a list of parameters that can be changed for each of your pages:


Visibility
~~~~~~~~~~

By default, pages are "invisible". To let people access them you should mark
them as "published".


Menus
~~~~~

Another option this view lets you tweak is whether or not the page should appear in
your site's navigation (that is, whether there should be a menu entry to reach it
or not)


Adding content to a page
------------------------

So far, our page doesn't do much. Make sure it's marked as "published", then
click on the page's "edit" button.

Ignore most of the interface for now and click the "view on site" button at the
top right-hand corner of the screen. As expected, your page is blank for the
time being, since our template is a really minimal one.

Let's get to it now then!

Press your browser's back button, so as to see the page's admin interface. If you followed
the tutorial so far, your template (``template_1.html``) defines two placeholders.
The admin interfaces shows you theses placeholders as sub menus:

|first-placeholders|

.. |first-placeholders| image:: ../../images/first-placeholders.png

Scroll down the "Available plugins" drop-down list. This displays the plugins you
added to your :setting:`django:INSTALLED_APPS` settings. Choose the "text" plugin in the drop-down,
then press the "Add" button. If the "text" plugin is not listed, you need to add
'djangocms_text_ckeditor' to your :setting:`django:INSTALLED_APPS` settings.

The right part of the plugin area displays a rich text editor (`TinyMCE`_).

In the editor, type in some text and then press the "Save" button.

The new text is only visible on the draft copy so far, but you can see it by using the
top button "Preview draft". If you use the "View on site" button instead, you can see that the
page is still blank to the normal users.

To publish the changes you have made, click on the "Publish draft" button.
Go back to your website using the top right-hand "View on site" button. That's it!

|hello-cms-world|

.. |hello-cms-world| image:: ../../images/hello-cms-world.png


Where to go from here
---------------------

Congratulations, you now have a fully functional CMS! Feel free to play around
with the different plugins provided out of the box and to build great websites!

You can continue the tutorial with :doc:`templates`


.. _TinyMCE: http://tinymce.moxiecode.com/

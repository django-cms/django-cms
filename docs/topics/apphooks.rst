.. _about_apphooks:

##############################
Application hooks ("apphooks")
##############################

An Application Hook, usually simply referred to as an apphook, is a way of attaching
the functionality of some other application to a django CMS page. It's a convenient way
of integrating other applications into a django CMS site.

For example, suppose you have an application that maintains and publishes information
about Olympic records. You could add this application to your site's ``urls.py`` (before
the django CMS URLs pattern), so that users will find it at ``/records``.

However, although it would thus be integrated into your *project*, it would not be
fully integrated into django CMS, for example:

* django CMS would not be aware of it, and - for example - would allow your users to create a CMS page with the same
  ``/records`` slug, that could never be reached.
* The application's pages won't automatically appear in your site's menus.
* The application's pages won't be able to take advantage of the CMS's publishing
  workflow, permissions or other functionality.

Apphooks offer a more complete way of integrating other applications, by attaching them
to a CMS page. In this case, the attached application takes over the page and its URL
(and all the URLs below it, such as ``/records/1984``).

The application can be served at a URL defined by the content managers, and easily moved
around in the site structure.

The *Advanced settings* of a CMS page provides an *Application* field. :ref:`Adding an apphook class <apphooks_how_to>` to the
application will allow it to be selected in this field.


*********************************
Multiple apphooks per application
*********************************

It's possible for an application to be added multiple times, to different pages. See :ref:`multi_apphook` for more.

Also possible to provide **multiple apphook configurations**:


**********************
Apphook configurations
**********************

You may require the same application to behave differently in different locations on your site. For example, the Olympic
Records application may be required to publish athletics results at one location, but cycling results at another, and so on.

An :ref:`apphook configuration <apphook_configurations>` class allows the site editors to create multiple configuration
instances that specify the behaviour. The kind of configuration available is presented in an admin form, and determined by the
application developer.

..  important::

    It's important to understand that an apphook (and therefore also an apphook configuration)
    serves no function until it is attached to a page - and until the page is **published**, the
    application will be unable to fulfil any publishing function.

    Also note that the apphook "swallows" all URLs below that of the page, handing them over to the
    attached application. If you have any child pages of the apphooked page, django CMS will not be
    able to serve them reliably.




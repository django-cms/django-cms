.. _touch:

Using touch-screen devices with django CMS
==========================================

.. important::

    These notes about touch interface support apply only to the **django CMS admin and
    editing interfaces**. The visitor-facing published site is **wholly independent** of
    this, and the responsibility of the site developer.

General
-------

django CMS has made extensive use of double-click functionality, which lacks an exact
equivalent in touch-screen interfaces. The touch interface will interpret taps and
touches in an intelligent way.

Depending on the context, a tap will be interpreted to mean *open for editing* (that is,
the equivalent of a double-click), or to mean *select* (the equivalent of a single
click), according to what makes sense in that context.

Similarly, in some contexts similar interactions may *drag* objects, or may *scroll*
them, depending on what makes most sense. Sometimes, the two behaviours will be present
in the same view, for example in the page list, where certain areas are draggable (for
page re-ordering) while other parts of the page can be used for scrolling.

In general, the chosen behaviour is reasonable for a particular object, context or
portion of the screen, and in practice is quicker and easier to apprehend simply by
using it than it is to explain.

Pop-up help text will refer to clicking or tapping depending on the device being used.

Be aware that some hover-related user hints are simply not available to touch interface
users.

.. _device-support:

Device support
--------------

Smaller devices such as most phones are too small to be adequately usable. For example,
your Apple Watch is sadly unlikely to provide a very good django CMS editing experience.

Older devices will often lack the performance to support a usefully responsive frontend
editing/administration interface.

The following devices are known to work well, so newer devices and more powerful models
should also be suitable:

- iOS: Apple iPad Air 1, Mini 4
- Android: Sony Xperia Z2 Tablet, Samsung Galaxy Tab 4
- Windows 10: Microsoft Surface

We welcome feedback about specific devices.

Your site's frontend
--------------------

django CMS's toolbar and frontend editing architecture rely on good practices in your
own frontend code. To work well with django CMS's responsive management framework, your
own site should be friendly towards multiple devices.

Whether you use your own frontend code or a framework such as Bootstrap 3 or Foundation,
be aware that problems in your CSS or markup can affect django CMS editing modes, and
this will become especially apparent to users of mobile/hand-held devices.

Known issues
------------

General issues
~~~~~~~~~~~~~~

- Editing links that lack sufficient padding is currently difficult or impossible using
  touch-screens.
- Similarly, other areas of a page where the visible content is composed entirely of
  links with minimal padding around them can be difficult or impossible to open for
  editing by tapping. This can affect the navigation menu (double-clicking on the
  navigation menu opens the page list).
- Adding links is known to be problematic on some Android devices, because of the
  behaviour of the keyboard.
- On some devices, managing django CMS in the browser's *private* (also known as
  *incognito*) mode can have significant performance implications.

  This is because local storage is not available in this mode, and user state must be
  stored in a Django session, which is much less efficient.

  This is an unusual use case, and should not affect many users.

CKEditor issues
~~~~~~~~~~~~~~~

- Scrolling on narrow devices, especially when opening the keyboard inside the CKEditor,
  does not always work ideally - sometimes the keyboard can appear in the wrong place
  on-screen.
- Sometimes the CKEditor moves unexpectedly on-screen in use.
- Sometimes in Safari on iOS devices, a rendering bug will apparently truncate or
  reposition portions of the toolbar when the CKEditor is opened - even though sections
  may appear to missing or moved, they can still be activated by touching the part of
  the screen where they should have been found.

Django Admin issues
~~~~~~~~~~~~~~~~~~~

- In the page tree, the first touch on the page opens the keyboard which may be
  undesirable. This happens because Django automatically focuses the search form input.

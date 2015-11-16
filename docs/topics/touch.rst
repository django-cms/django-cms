.. _touch:

##########################################
Using touch-screen devices with django CMS
##########################################

.. important::

    These notes about touch interface support apply only to the **django CMS admin and editing
    interfaces**. The visitor-facing published site is **wholly independent** of this, and the
    responsibility of the site developer.


*******
General
*******

django CMS has made extensive use of double-click functionality, which lacks an exact equivalent in
touch-screen interfaces. The touch interface will interpret taps and touches in an intelligent way.

Depending on the context, a tap will be interpreted to mean *open for editing* (that is, the
equivalent of a double-click), or to mean *select* (the equivalent of a single click), according to
what makes sense in that context.

Similarly, in some contexts similar interactions may *drag* objects, or may *scroll* them,
depending on what makes most sense. Sometimes, the two behaviours will be present in the same view,
for example in the page list, where certain areas are draggable (for page re-ordering) while other
parts of the page can be used for scrolling.

In general, the chosen behaviour is reasonable for a particular object, context or portion of the
screen, and in practice is quicker and easier to apprehend simply by using it than it is to explain.

Pop-up help text will refer to clicking or tapping depending on the device being used.

Be aware that some hover-related user hints are simply not available to touch interface users. For
example, the overlay (formerly, the *sideframe*) can be adjusted for width by dragging its edge,
but this is not indicated in a touch-screen interface.


.. _device-support:

**************
Device support
**************

Smaller devices such as most phones are too small to be adequately usable. For example, your Apple
Watch is sadly unlikely to provide a very good django CMS editing experience.

Older devices will often lack the performance to support a usefully responsive frontend
editing/administration interface.

The following devices are known to work well, so newer devices and more powerful models should also
be suitable:

* iOS: Apple iPad Air 1, Mini 4
* Android: Sony Xperia Z2 Tablet, Samsung Galaxy Tab 4
* Windows 10: Microsoft Surface

We welcome feedback about specific devices.


********************
Your site's frontend
********************

django CMS's toolbar and frontend editing architecture rely on good practices in your own frontend
code. To work well with django CMS's responsive management framework, your own site should be
friendly towards multiple devices.

Whether you use your own frontend code or a framework such as Bootstrap 3 or Foundation, be aware
that problems in your CSS or markup can affect django CMS editing modes, and this will become
especially apparent to users of mobile/hand-held devices.

#################
Site-wide content
#################

So far, we have been able to add content to particular parts of the site, and in some cases, re-use
it with plugins.

Sometimes it's useful to have content that appears *everywhere* on a site, like a header or a
footer. So let's add both to our site.


*************************************************
Add a site-wide header using a static placeholder
*************************************************

.. todo:: we need to add a "header" static placeholder to the template

You can do this sort of thing with **Static placeholders**. You have already used placeholders, for
example when you :ref:`added a News plugin <use-news-plugin>` to the home page. A static
placeholder's contents will appear in every page, in the same place.

We'll add an image to the top of every page on the site, by adding it to the *Header* static
placeholder.

.. todo:: add image of "Head" static placeholder with tooltip "This is a static placeholder"

.. todo:: We should provide a suitable example image

Anything that is placed in there will be displayed at the top of every page. You can also edit it
the placeholder on any page, so:

#.  switch to *Edit* mode
#.  select *Structure* view
#.  Select the **Add plugin** icon |add-plugin-icon|.
#.  Choose *Image* from the list of available plugin types.
#.  Add a wide, short image that will function as a suitable header


.. todo:: show result in Content mode


*************************************************
Add a site-wide footer using a static placeholder
*************************************************


We should also add a footer, in just the same way - this time, add something to the *Footer* static placeholder.


.. todo:: add image of "Footer" static placeholder with tooltip "This is a static placeholder"

.. |add-plugin-icon| image:: /user/tutorial/images/add-plugin-icon.png
   :alt: 'add plugin'

#.  Select the **Add plugin** icon |add-plugin-icon|.
#.  Choose *Text* from the list of available plugin types.

    .. tip::

        Text
            City Bicycle Services, because bicycles need love and attention too.

#.  Hit **Save**
#.  Switch back to *Content* mode.

You'll now see the footer on your page in fact, on *every* page, thanks to the static placeholder.

.. todo:: add image of the Footer in an actual page

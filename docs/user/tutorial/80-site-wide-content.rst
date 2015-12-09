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

You can do this sort of thing with **Static placeholders**. You have already used placeholders, for
example when you :ref:`added a News plugin <use-news-plugin>` to the home page. A static
placeholder's contents will appear in every page, in the same place.

We'll add an image to the top of every page on the site, by adding it to the *Header* static
placeholder.

.. image:: /user/tutorial/images/header_static_placeholder.png
   :alt: Header static placeholder
   :width: 100%
   :align: center

Anything that is placed in there will be displayed at the top of every page. You can also edit it
the placeholder on any page, so:

#.  Switch to *Edit* mode |Edit button|

    .. |Edit button| image:: /user/tutorial/images/edit-button.png
       :alt: Edit button
       :width: 50px

#.  Select *Structure* view |structure-button|

    .. |structure-button| image:: /user/tutorial/images/structure-content.png
       :alt: 'Structure button'
       :width: 150px

#.  Select the **Add plugin** icon.

    |add-plugin-icon|

    .. |add-plugin-icon| image:: /user/tutorial/images/add-plugin-icon.png
       :alt: 'Add plugin'
       :width: 350px

#.  Choose *Image* from the list of available plugin types.

    |choose-image-plugin|

    .. |choose-image-plugin| image:: /user/tutorial/images/choose_image_plugin.png
       :alt: 'Choose image plugin'
       :width: 50%


#.  Add a wide, short image that will function as a suitable header.

    .. image:: /user/tutorial/images/home_overview.png
       :alt: Choose image plugin
       :width: 100%
       :align: center

*************************************************
Add a site-wide footer using a static placeholder
*************************************************


We should also add a footer, in just the same way - this time, add something to the *Footer* static placeholder.

#.  Select the **Add plugin** icon.

    |add-plugin-icon|

#.  Choose *Text* from the list of available plugin types.

    .. tip::

        Text
            City Bicycle Services, because bicycles need love and attention too.

    |choose_text|

    .. |choose_text| image:: /user/tutorial/images/choose_text.png
       :alt: Choose text
       :width: 60%

#.  Hit **Save**

    .. image:: /user/tutorial/images/add_text.png
       :alt: Choose text
       :width: 100%
       :align: center

#.  Switch back to *Content* mode.

You'll now see the footer on your page in fact, on *every* page, thanks to the static placeholder.

    .. image:: /user/tutorial/images/show_static_footer.png
       :alt: Choose text
       :width: 100%
       :align: center

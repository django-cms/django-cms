######################
Changing page settings
######################

The django CMS toolbar offers other useful editing tools.

Switch to *Edit* mode on one of your pages, and from the toolbar select *Page* > *Page settings...*.
The *Change page* dialog that opens allows you to manage key settings for your page.

.. image:: /user/tutorial/images/change-page-dialog.png
   :alt: the 'Change page' dialog
   :align: center
   :width: 50%


Some key settings:

* *Slug*: The page's *slug* is used to form its URL. For example, a page *Lenses* that is a
  sub-page of *Photography* might have a URL that ends ``photography/lenses``. You can change the
  automatically-generated slug of a page if you wish to. Keep slugs short and meaningful, as they
  are useful to human beings and search engines alike. You can

* *Menu Title*: If you have a page called *Photography: theory and practice*, you might not want
  the whole title to appear in menus - shortening it to *Photography* would make more sense.

* *Page Title*: By default, a page's ``<title>`` element is taken from the *Title*, but you can
  override this here. The ``<title>`` element isn't displayed on the page, but is used by search
  engines and web browsers - as far as they are concerned, it's the page's real title.

* *Description meta tag*: A short piece of text that will be used by search engines (and displayed
  in lists of search results) and other indexing systems.

There are also some *Advanced Settings*, but you don't need to be concerned about these now.



resizable plugin for WYMeditor
##############################

The ``resizable`` plugin for WYMeditor_ enables vertical resizing of the
editor area. The plugin is based on the jQuery UI library.

Requirements
============
The following packages are required for using the WYMeditor ``resizable``
plugin:

* jQuery (tested with jQuery ``jquery-1.2.4a.js`` from ``jquery.ui`` package)
* WYMeditor SVN trunk (Revision: 482)
* jQuery-UI (tested with ``jquery.ui-1.5b2``)

It should be possible to use this plugin with ``WYMeditor-0.4`` but I have not
tried.

Download
========
You can download the WYMeditor ``resizable`` plugin here:

* wymeditor-resizable-plugin-0.2.tgz_
* wymeditor-resizable-plugin-0.1.tgz_ 

See the Changelog_ for more infos about the releases.

.. _wymeditor-resizable-plugin-0.2.tgz: http://pyjax.net/download/wymeditor-resizable-plugin-0.2.tgz
.. _wymeditor-resizable-plugin-0.1.tgz: http://pyjax.net/download/wymeditor-resizable-plugin-0.1.tgz

Installation
============
Just extract the downloaded archive into your WYMeditor's ``plugin``
directory.

Usage
=====
For general instructions on WYMeditor plugins please refer to the `WYMeditor
plugin page`_.

To use the ``resizable`` plugin simply include the plugin's JavaScript file in
your code. You **do not** need to include the jQuery UI files - this is done
automatically by the plugin (see `Internals`_)::

    <script type="text/javascript"
            src="/js/wymeditor/plugins/resizable/jquery.wymeditor.resizable.js">
    </script>

Make sure to adjust the ``src`` attribute to your needs, then initialize the
plugin in WYMeditor's ``postInit`` function::

    wymeditor({postInit: function(wym) {
                            wym.hovertools(); // other plugins...
                            wym.resizable({handles: "s,e",
                                           maxHeight: 600});
                         }
               })

The ``resizable`` plugin takes exactly one parameter, which is an object literal
containing the options of the plugin. The WYMeditor ``resizable`` plugin
supports all options of the jQuery UI ``resizable`` plugin. These are the
default values used by the plugin::

    handles: "s,e,se",
    minHeight: 250,
    maxHeight: 600

See the `jQuery UI resizable plugin docs`_ for a list of all options.

That's it! You are now able to resize the WYMeditor vertically, horizontally or
both, depending on your options.

..  _jQuery UI resizable plugin docs: http://docs.jquery.com/UI/Resizables

Internals
=========
The plugin takes care of loading the necessary jQuery UI files (``base`` and
``resizable``) from the same path the jQuery library was loaded. Here's how
it's done::

    // Get the jQuery path from the editor, stripping away the jQuery file.
    // see http://www.oreilly.com/catalog/regex/chapter/ch04.html
    // The match result array contains the path and the filename.
    var jQueryPath = wym.computeJqueryPath().match(/^(.*)\/(.*)$/)[1];

    // Make an array of the external JavaScript files required by the plugin.
    var jQueryPlugins = [jQueryPath + '/ui.base.js',
                         jQueryPath + '/ui.resizable.js'];
    
    // First get the jQuery UI base file
    $.getScript(jQueryPlugins[0]);

    // Get the jQuery UI resizeable plugin and then init the wymeditor resizable
    // plugin. It is import to do the initialisation after loading the    
    // necessary jQuery UI files has finished, otherwise the "resizable" method
    // would not be available.
    $.getScript(jQueryPlugins[1], function() {     
        jQuery(wym._box).resizable(final_options);
    });

An alternative approach would be to use an AJAX queue when getting the script
files to ensure that all jQuery files are loaded before the initialisation code
of the plugin is executed. There is an `jQuery AJAX queue plugin`_ which does
that. 

.. _jQuery AJAX queue plugin: http://plugins.jquery.com/project/ajaxqueue

Changelog
=========

0.2
---
- Added full support for all jQuery UI resizable plugin options.
- Refactored and documented code.
- Now contains a packed version (775 bytes).

0.1
---
- Initial release.

.. _WYMeditor:              http://www.wymeditor.org/
.. _WYMeditor plugin page:  http://trac.wymeditor.org/trac/wiki/0.4/Plugins

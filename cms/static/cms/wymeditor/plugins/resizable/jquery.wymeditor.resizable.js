/*
 * WYMeditor : what you see is What You Mean web-based editor
 * Copyright (c) 2005 - 2009 Jean-Francois Hovinne, http://www.wymeditor.org/
 * Dual licensed under the MIT (MIT-license.txt)
 * and GPL (GPL-license.txt) licenses.
 *
 * For further information visit:
 *        http://www.wymeditor.org/
 *
 * File Name:
 *        jquery.wymeditor.resizable.js
 *        resize plugin for WYMeditor
 *
 * File Authors:
 *        Peter Eschler (peschler _at_ gmail.com)
 *        Jean-Francois Hovinne - http://www.hovinne.com/
 *
 * Version:
 *        0.4
 *
 * Changelog:
 *
 * 0.4
 *     - Removed UI and UI.resizable scripts loading - see #167 (jfh).
 *
 * 0.3
 *     - Added 'iframeOriginalSize' and removed 'ui.instance' calls (jfh).
 *
 * 0.2
 *     - Added full support for all jQueryUI resizable plugin options.
 *     - Refactored and documented code.
 * 0.1
 *     - Initial release.
 */

/**
 * The resizable plugin makes the wymeditor box vertically resizable.
 * It it based on the ui.resizable.js plugin of the jQuery UI library.
 *
 * The WYMeditor resizable plugin supports all parameters of the jQueryUI
 * resizable plugin. The parameters are passed like this:
 *
 *         wym.resizable({ handles: "s,e",
 *                         maxHeight: 600 });
 *
 * DEPENDENCIES: jQuery UI, jQuery UI resizable
 *
 * @param options options for the plugin
 */
WYMeditor.editor.prototype.resizable = function(options) {

    var wym = this;
    var $iframe = jQuery(wym._box).find('iframe');
    var $iframe_div = jQuery(wym._box).find('.wym_iframe');
    var iframeOriginalSize = {};

    // Define some default options
    var default_options = {
        resize: function() {
          $iframe_div.height($iframe.height());
        },
        alsoResize: $iframe,
        handles: "s,e,se",
        minHeight: 250
    };

    // Merge given options with default options. Given options override
    // default ones.
    var final_options = jQuery.extend(default_options, options);

    if (jQuery.isFunction(jQuery.fn.resizable)) {
        jQuery(wym._box).resizable(final_options);
    } else {
        WYMeditor.console.error('Oops, jQuery UI.resizable unavailable.');
    }

};

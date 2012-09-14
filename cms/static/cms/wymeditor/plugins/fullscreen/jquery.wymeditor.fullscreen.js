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
 *        jquery.wymeditor.fullscreen.js
 *        Fullscreen plugin for WYMeditor
 *
 * File Authors:
 *        Luis Santos (luis.santos a-t openquest dotpt)
 *        Jonatan Lundin (jonatan.lundin a-t gmail dotcom)
 *        Gerd Riesselmann (gerd a-t gyro-php dot org) : Fixed issue with new skin layout
 */

//Extend WYMeditor
WYMeditor.editor.prototype.fullscreen = function() {
    var wym = this,
        $box = jQuery(this._box),
        $iframe = jQuery(this._iframe),
        $overlay = null,
        $window = jQuery(window),

        editorMargin = 15;     // Margin from window (without padding)


    //construct the button's html
    var html = '' +
        "<li class='wym_tools_fullscreen'>" +
            "<a name='Fullscreen' href='#' " +
                "style='background-image: url(" +
                    wym._options.basePath +
                    "plugins/fullscreen/icon_fullscreen.gif)'>" +
                "Fullscreen" +
            "</a>" +
        "</li>";
    //add the button to the tools box
    $box.find(wym._options.toolsSelector + wym._options.toolsListSelector)
        .append(html);

    function resize () {
        // Calculate margins
        var uiHeight = $box.outerHeight(true) - $iframe.outerHeight(true);
        var editorPadding = $box.outerWidth() - $box.width();

        // Calculate heights
        var screenHeight = $window.height();
        var iframeHeight = (screenHeight - uiHeight - (editorMargin * 2)) + 'px';

        // Calculate witdths
        var screenWidth = $window.width();
        var boxWidth = (screenWidth - editorPadding - (editorMargin * 2)) + 'px';

        $box.css('width', boxWidth);
        $iframe.css('height', iframeHeight);
        $overlay.css({
            'height': screenHeight + 'px',
            'width': screenWidth + 'px'
        });
    }

    //handle click event
    $box.find('li.wym_tools_fullscreen a').click(function() {
        if ($box.css('position') != 'fixed') {
            // Store previous inline styles
            $box.data('wym-inline-css', $box.attr('style'));
            $iframe.data('wym-inline-css', $iframe.attr('style'));

            // Create overlay
            $overlay = jQuery('<div id="wym-fullscreen-overlay"></div>')
                .appendTo('body').css({
                    'position': 'fixed',
                    'background-color': 'rgb(0, 0, 0)',
                    'opacity': '0.75',
                    'z-index': '98',
                    'top': '0px',
                    'left': '0px'
                });

            // Possition the editor
            $box.css({
                'position': 'fixed',
                'z-index': '99',
                'top': editorMargin + 'px',
                'left': editorMargin + 'px'
            });

            // Bind event listeners
            $window.bind('resize', resize);
            $box.find('li.wym_tools_html a').bind('click', resize);

            // Force resize
            resize();
        } else {
            // Unbind event listeners
            $window.unbind('resize', resize);
            $box.find('li.wym_tools_html a').unbind('click', resize);

            // Remove inline styles
            $box.css({
                'position': 'static',
                'z-index': '',
                'width': '',
                'top': '',
                'left': ''
            });
            $iframe.css('height', '');

            // Remove overlay
            $overlay.remove();
            $overlay = null;

            // Retore previous inline styles
            $box.attr('style', $box.data('wym-inline-css'));
            $iframe.attr('style', $iframe.data('wym-inline-css'));
        }

        return false;
    });
};

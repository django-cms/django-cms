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
    *        jquery.wymeditor.tidy.js
    *        HTML Tidy plugin for WYMeditor
    *
    * File Authors:
    *        Jean-Francois Hovinne (jf.hovinne a-t wymeditor dotorg)
    */

//WymTidy constructor
function WymTidy(options, wym) {
    var wand_url = wym._options.basePath + "plugins/tidy/wand.png";
    options = jQuery.extend({
        sUrl:            wym._options.basePath + "plugins/tidy/tidy.php",
        sButtonHtml:     "" +
            "<li class='wym_tools_tidy'>" +
                "<a name='CleanUp' href='#'" +
                    " style='background-image: url(" + wand_url +")'>" +
                    "Clean up HTML" +
                "</a>" +
            "</li>",

        sButtonSelector: "li.wym_tools_tidy a"

    }, options);

    this._options = options;
    this._wym = wym;
}

//Extend WYMeditor
WYMeditor.editor.prototype.tidy = function(options) {
    var tidy = new WymTidy(options, this);
    return tidy;
};


//WymTidy initialization
WymTidy.prototype.init = function() {
    var tidy = this;

    jQuery(this._wym._box).find(
        this._wym._options.toolsSelector + this._wym._options.toolsListSelector)
        .append(this._options.sButtonHtml);

    //handle click event
    jQuery(this._wym._box).find(this._options.sButtonSelector).click(function() {
        tidy.cleanup();
        return(false);
    });
};

//WymTidy cleanup
WymTidy.prototype.cleanup = function() {
    var wym = this._wym;
    var html = "<html><body>" + wym.xhtml() + "</body></html>";

    jQuery.post(this._options.sUrl, { html: html}, function(data) {
        if (data.length > 0 && data != '0') {
            if (data.indexOf("<?php") === 0) {
                wym.status("Ooops... Is PHP installed?");
            } else {
                wym.html(data);
                wym.status("HTML has been cleaned up.");
            }
        } else {
            wym.status("An error occurred.");
        }
    });
};

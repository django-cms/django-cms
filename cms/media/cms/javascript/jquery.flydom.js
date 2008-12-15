/**
 * jQuery Plugin FlyDOM v3.0
 *
 * Create DOM elements on the fly and automatically append or prepend them to another DOM object.
 * There are also template functions (tplAppend and tplPrepend) that can take a simple HTML structure
 * and apply a JSON object to it to make creating layouts MUCH easier.
 *
 * This plugin was inspired by "Oslow" [http://mg.to/2006/02/27/easy-dom-creation-for-jquery-and-prototype#comment-176],
 * and since I could not get his code to work, I decided I write my own plugin. My hope is that this
 * version will be easier to understand and maintain with future versions of jQuery.
 *
 * Copyright (c) 2007 Ken Stanley [dohpaz at gmail dot com]
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 *
 * @version     3.0.5
 *
 * @author      Ken Stanley [dohpaz at gmail dot com]
 * @copyright   (C) 2007. All rights reserved.
 *
 * @license     http://www.opensource.org/licenses/mit-license.php
 * @license     http://www.opensource.org/licenses/gpl-license.php
 *
 * @package     jQuery Plugins
 * @subpackage  FlyDOM
 *
 * @todo        Cache basic elements that are created, and if an already existing basic element is
 *              asked to be created an additional time, use a copy of the cached element to build from.
 */

/**
 * Create DOM elements on the fly and automatically append them to the current DOM obejct
 *
 * @uses    jQuery
 * @uses    function convertCamel()
 *
 * @param   string  element - The name of the DOM element to create (i.e., img, table, a, etc)
 * @param   object  attrs   - An optional object of attributes to apply to the element
 * @param   array   content - An optional array of content (or element children) to append to element
 *
 * @return  jQuery  element - The jQuery object representing the new element
 *
 * @since   1.0
 */
jQuery.fn.createAppend = function(element, attrs, content)
{

    // This helps me remember what 'this' is later on.
    var parentElement = this[0];

    // I *hate* exceptions
    if (jQuery.browser.msie && element == 'input' && attrs.type) {

        // IE will not allow you to modify the type attribute after an element is
        // created, so we must create the input element with the type attribute.
        var element = document.createElement('<' + element + ' type="' + attrs.type + '" />');

    } else {

        // This is for every other element
        var element = document.createElement(element);

    };

    // Check to see if we are using IE, and trying to append a TR to a TABLE.
    if (jQuery.browser.msie && parentElement.nodeName.toLowerCase() == 'table' && element.nodeName.toLowerCase() == 'tr') {

        // Check to see if we already have a tbody element in the table
        if (parentElement.parentNode.getElementsByTagName('tbody')[0]) {

            // Use the existing tbody
            var tbody = parentElement.getElementsByTagName('tbody')[0];

        } else {

            // Create a new tbody
            var tbody = parentElement.appendChild(document.createElement('tbody'));

        };

        // Append our TR to our TBODY and continue
        var element = tbody.appendChild(element);

    } else {

        // Add the element directly to the parentElement
        var element = parentElement.appendChild(element);

    };

    // Parse our attributes into our new element
    element = __FlyDOM_parseAttrs(element, attrs);

    // Determine what to do with our red-headed stepchild.
    if (typeof content == 'object' && content != null) {

        // Loop through content and create child elements
        for (var i = 0; i < content.length; i = i + 3) {

            jQuery(element).createAppend(content[i], content[i + 1] || {}, content[i + 2] || []);

        };

    // Add as text
    } else if (content != null) {

        element = __FlyDOM_setText(element, content);

    };

    // Return the newly appended element to the caller
    return jQuery(element);

}

/**
 * Create DOM elements on the fly and automatically prepend them to the current DOM obejct
 *
 * @uses    jQuery
 * @uses    createAppend()
 *
 * @param   string  element - The name of the DOM element to create (i.e., img, table, a, etc)
 * @param   object  attrs   - An optional object of attributes to apply to the element
 * @param   array   content - An optional array of content (or element children) to append to element
 * @return  jQuery  element - The jQuery object representing the new element
 *
 * @since   1.0
 */
jQuery.fn.createPrepend = function(element, attrs, content)
{

    // Create our DOM element
    var element     = document.createElement(element);

    // If we do not have a child node, just append the new element
    if (this[0].hasChildNodes() == false) {

        var element = this[0].appendChild(element);

    };

    // Parse our attributes into our new element
    element = __FlyDOM_parseAttrs(element, attrs);

    // Determine what to do with our red-headed stepchild.
    if (typeof content == 'object' && content != null) {

        // Loop through the content and append any children
        for (var i = 0; i < content.length; i = i + 3) {

            jQuery(element).createAppend(content[i], content[i + 1] || {}, content[i + 2] || []);

        };

    // Add as text
    } else if (content != null) {

        element = __FlyDOM_setText(element, content);

    };

    // Here we check to see if this element has children, and if so,
    // we will insert it before the first child node.
    if (this[0].hasChildNodes() == true) {

        var element = this[0].insertBefore(element, this[0].firstChild);

    };

    // Return the newly appended element to the caller
    return jQuery(element);

}

/**
 * Create DOM elements on the fly using a simple template system, and then append the new element(s) to
 * the end of the calling object.
 *
 * @uses jQuery
 * @uses createAppend()
 *
 * @param   object  json    - A JSON-formatted object that holds the dynamic data
 * @param   array   tpl     - An array containing the element(s) to append to the caller
 * @return  jQuery  self    - The jQuery object representing the new element(s)
 *
 * @since   2.0
 */
jQuery.fn.tplAppend = function(json, tpl)
{

    // Make sure that we have an array to work with
    if (json.constructor != Array) { json = [ json ]; };

    // Don't try to do anything if we have nothing to do
    if (json.length == 0) { return false; };

    // Loop through our JSON "rows"
    for (var i = 0; i < json.length; i++) {

        // Apply the data to the template and get our results
        var results = tpl.apply(json[i]);

        // Just like with createAppend/createPrepend; this is the best way to
        // loop through and create our new element(s).
        for (var j = 0; j < results.length; j = j + 3) {

            jQuery(this).createAppend(results[j], results[j + 1], results[j + 2]);

        };

    };

    // Return ourself for chaining
    return self;

}

/**
 * Create DOM elements on the fly using a simple template system, and then prepend the new element(s) to
 * the beginning of the calling object. The elements will first be appended to a temporary div container,
 * and then prepended before the first child of the parent element.
 *
 * @uses jQuery
 * @uses createAppend()
 *
 * @param   object  json    - A JSON-formatted object that holds the dynamic data
 * @param   array   tpl     - An array containing the element(s) to prepend to the caller
 * @return  jQuery  self    - The jQuery object representing the new element(s)
 *
 * @since   2.0
 */
jQuery.fn.tplPrepend = function(json, tpl) {

    // This will allow 'this' to go inside of a .each() loop
    var self = this[0];

    // Make sure that we have an array to work with
    if (json.constructor != Array) { json = [ json ]; };

    // Don't try to do anything if we have nothing to do
    if (json.length == 0) { return false; };

    // Here we create a div and insert it before the element we're
    // prepending to
    var div = document.createElement('div');

    // Loop through our JSON "rows"
    for (var i = 0; i < json.length; i++) {

        // Apply the data to the template and get our results
        var results = tpl.apply(json[i]);

        // Just like with createAppend/createPrepend; this is the best way to
        // loop through and create our new element(s).
        for (var j = 0; j < results.length; j = j + 3) {

            jQuery(div).createAppend(results[j], results[j + 1], results[j + 2]);

        };

    };

    // Apply each child node of the div container starting from the last one
    // This will ensure that all elements get applied as expected, and still
    // be readable from top to bottom.
    for (i = div.childNodes.length - 1; i >= 0; i--) {

        if (jQuery.browser.msie && self.nodeName.toLowerCase() == 'table' && div.childNodes[i].nodeName.toLowerCase() == 'tr') {

            if (self.getElementsByTagName('tbody')[0]) {

                var tbodyElement = self.getElementsByTagName('tbody')[0];
                tbodyElement.insertBefore(div.childNodes[i], tbodyElement.firstChild);

            } else {

                var tbodyElement = self.insertBefore(document.createElement('tbody'), self.firstChild);
                tbodyElement.appendChild(tbodyElement.appendChild(div.childNodes[i]));

            };
        } else {

            self.insertBefore(div.childNodes[i], self.firstChild);

        };

    };

    // Return ourself for chaining
    return jQuery(self);

};

/**
 * Convert a hyphenated set of words into one camel cased word. For example,
 * the hyphenated set of words 'border-left-width' would turn into 'borderLeftWidth'.
 *
 * @param   string  hyphenatedText  - The text to convert into camel case
 *
 * @return  string
 *
 * @since   3.0
 */
String.prototype.toCamelCase = function()
{

    var self = this;

    if (self.indexOf('-') > 0) {

        var parts = self.split('-');

        // Start the new text with the first word
        self = parts[0];

        // We skip over the first word, and capitalize
        // each word after.
        for (i = 1; i < parts.length; i++) {

            // Uppercase the first letter, and ensure the rest is lowercase.
            self += parts[i].substr(0, 1).toUpperCase() + parts[i].substr(1).toLowerCase();

        };

    };

    return self;

};

/**
 * Trims the whitespace from the beginning and end of a string.
 * This is the same exact method from the jQuery library, but
 * is put here to avoid having to call jQuery to do this one
 * simple thing.
 *
 * @param   string  text    - The text to trim
 *
 * @return  string
 *
 * @since   3.0
 */
String.prototype.trim = function()
{

    return this.replace(/^\s+|\s+$/g, '');

};

/**
 * Parse the attributes of element and return the element modified with
 * attrs.
 *
 * @uses    function toCamelCase()
 * @uses    function trim()
 *
 * @return  element
 *
 * @since   3.0
 */
__FlyDOM_parseAttrs = function(element, attrs)
{

    // Attach any attributes for this element
    for (attr in attrs) {

        // Break the styles up into a parameters array
        var attrName    = attr;
        var attrValue   = attrs[attr];

        switch (attrName) {

            // Styles are special because the DOM holds style information in an object.
            case 'style':

                if (typeof attrValue == 'string') {

                    var params = attrValue.split(';');

                    // Loop through each set of properties
                    for (var i = 0; i < params.length; i++) {

                        // Check to make sure someone (like myself) didn't end the value with a
                        // semi-colon.
                        if (params[i].trim() != '') {

                            // This is just to ease my burden of reading and typing :)
                            var styleName   = params[i].split(':')[0].trim();
                            var styleValue  = params[i].split(':')[1].trim();

                            // Take into account that styles with hyphens in the name need
                            // to be converted into camelCase.
                            styleName = styleName.toCamelCase();

                            // Don't try to apply the style if it is empty (this happens if
                            // the value of the attribute ends with a semi-colon.
                            if (styleName != '') {

                                // Apply each name/value pair, after removing any whitespace
                                element.style[styleName] = styleValue;

                            };

                        };

                    };

                } else if (typeof attrValue == 'object') {

                    for (styleName in attrValue) {

                        // Take into account that styles with hyphens in the name need
                        // to be converted into camelCase.
                        var styleNameCamel = styleName.toCamelCase();

                        if (styleName.trim() != '') {

                            element.style[styleNameCamel] = attrValue[styleName];

                        };

                    };

                };
                break;

            // Other attributes are treated as strings.
            default:

                // Check for any on* events
                if (attrName.substr(0, 2) == 'on') {

                    // Get the type of on event
                    var event = attrName.substr(2);

                    // Determine whether we need to create an anonymous function,
                    // or if the user was kind enough to do it for us.
                    attrValue = (typeof attrValue != 'function') ? eval('function() { ' + attrValue + '}') : attrValue;

                    // Bind the function to the event
                    jQuery(element).bind(event, attrValue);

                } else {

                    // Everything else (I hope) :)
                    element[attrName.toCamelCase()] = attrValue;

                }

        };

    };

    return element;

};

/**
 * Determines whether content should be treated as HTML or plain text,
 * and appended to element.
 *
 * @return  element
 *
 * @since   3.0
 */
__FlyDOM_setText = function(element, content)
{

    // Check for HTML tags or HTML entities.
    var isHtml = /(<\S[^><]*>)|(&.+;)/g;

    // Determine whether the text contains any HTML or entities
    // An exception is made for <textarea></textarea>; all text must be treated as text.
    if (content.match(isHtml) != null && element.tagName.toUpperCase() != 'TEXTAREA') {

        element.innerHTML = content;

    } else {

        // Create a text node from the content
        var textNode = document.createTextNode(content);

        // Add the text node to the element
        element.appendChild(textNode);

    };

    return element;

};
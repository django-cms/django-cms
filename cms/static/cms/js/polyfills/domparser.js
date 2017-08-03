/*
 * DOMParser HTML extension
 * 2012-09-04
 *
 * By Eli Grey, http://eligrey.com
 * Public domain.
 * NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.
 */

/* @source https://gist.github.com/1129031 */
/* global document, DOMParser*/

(function(DOMParser) {
    'use strict';

    var DOMParser_proto = DOMParser.prototype;
    var real_parseFromString = DOMParser_proto.parseFromString;

    // Firefox/Opera/IE throw errors on unsupported types
    try {
        // WebKit returns null on unsupported types
        if (new DOMParser().parseFromString('', 'text/html')) {
            // text/html parsing is natively supported
            return;
        }
    } catch (ex) {}

    // eslint-disable-next-line complexity
    DOMParser_proto.parseFromString = function(markup, type) {
        if (/^\s*text\/html\s*(?:;|$)/i.test(type)) {
            var doc = document.implementation.createHTMLDocument('');

            // Note: IE 9 doesn't support writing innerHTML on this node
            try {
                doc.head.innerHTML = '';
            } catch (ex) {}

            // Note: make this polyfill behave closer to native domparser
            if (markup.indexOf('<!') > -1) {
                try {
                    doc.documentElement.innerHTML = markup;
                } catch (ex) {}
            } else if (
                markup.indexOf('<title') > -1 ||
                markup.indexOf('<meta') > -1 ||
                markup.indexOf('<link') > -1 ||
                markup.indexOf('<script') > -1 ||
                markup.indexOf('<style') > -1
            ) {
                try {
                    doc.head.innerHTML = markup;
                } catch (ex) {}
            } else {
                doc.body.innerHTML = markup;
            }
            return doc;
        }

        return real_parseFromString.apply(this, arguments);
    };
})(DOMParser);

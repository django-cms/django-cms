/*##################################################|*/
/* #CMS# */

// ensuring django namespace is set correctly
var django = window.django || undefined;

// ensuring jQuery namespace is set correctly
var jQuery = (django) ? django.jQuery : window.jQuery || undefined;

// ensuring Class namespace is set correctly
var Class = window.Class || undefined;

// ensuring CMS namespace is set correctly
var CMS = {
	'$': (jQuery) ? jQuery.noConflict() : undefined,
	'Class': (Class) ? Class.noConflict() : undefined,
	'API': {}
};

/*##################################################|*/
/* #CMS.API# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * CNS.API.Helpers
	 * @version: 1.0.0
	 * @public_methods:
	 *	- CMS.API.Helpers.reloadBrowser();
	 */
	CMS.API.Helpers = {

		// redirects to a specific url or reloads browser
		reloadBrowser: function (url, timeout) {
			// add timeout if provided
			setTimeout(function () {
				(url) ? window.location.href = url : window.location.reload();
			}, timeout || 0);
		},

		// disable multiple form submissions
		preventSubmit: function () {
			$('form').submit(function () {
				$('input[type="submit"]').attr('disabled', 'disabled');
			});
		}

	};

	// autoinits
	CMS.API.Helpers.preventSubmit();

});
})(CMS.$);
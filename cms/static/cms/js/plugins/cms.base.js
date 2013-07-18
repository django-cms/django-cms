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
			// is there a parent window?
			parent = (window.parent) ? window.parent : window;
			// add timeout if provided
			parent.setTimeout(function () {
				(url) ? parent.location.href = url : parent.location.reload();
			}, timeout || 0);
		},

		// disable multiple form submissions
		preventSubmit: function () {
			$('form').submit(function () {
				// we cannot use disabled as the name action will be ignored
				$('input[type="submit"]').bind('click', function (e) {
					e.preventDefault();
				}).css('opacity', 0.5);
			});
		},

		// fixes csrf behaviour
		csrf: function (csrf_token) {
			$.ajaxSetup({
				beforeSend: function (xhr) {
					// set csrf_token
					xhr.setRequestHeader("X-CSRFToken", csrf_token);
				}
			});
		}

	};

	// autoinits
	CMS.API.Helpers.preventSubmit();

});
})(CMS.$);
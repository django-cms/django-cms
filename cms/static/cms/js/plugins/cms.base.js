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
	 *	- CMS.API.Helpers.getUrl(urlString);
	 *	- CMS.API.Helpers.setUrl(urlString, options);
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
				$('input[type="submit"]').attr('disabled', 'disabled');
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
		},

		getUrl: function(str) {
			var	o = {
				'strictMode': false,
				'key': ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","anchor"],
				'q': { 'name': 'queryKey', 'parser': /(?:^|&)([^&=]*)=?([^&]*)/g },
				'parser': {
					'strict': /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
					'loose':  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
				}
			};

			var m = o.parser[o.strictMode ? 'strict' : 'loose'].exec(str), uri = {}, i = 14;

			while(i--) uri[o.key[i]] = m[i] || '';

			uri[o.q.name] = {};
			uri[o.key[12]].replace(o.q.parser, function ($0, $1, $2) {
				if($1) { uri[o.q.name][$1] = $2; }
			});

			return uri;
		},

		setUrl: function (str, options) {
			var uri = str;

			// now we neet to get the partials of the element
			var getUrlObj = this.getUrl(uri);
			var query = getUrlObj.queryKey;
			var serialized = '';
			var index = 0;

			// we could loop the query and replace the param at the right place
			// but instead of replacing it just append it to the end of the query so its more visible
			if(options && options.removeParam) delete query[options.removeParam];
			if(options && options.addParam) query[options.addParam.split('=')[0]] = options.addParam.split('=')[1];

			$.each(query, function (key, value) {
				// add &
				if(index != 0) serialized += '&';
				// if a value is given attach it
				serialized += (value) ? (key + '=' + value) : (key);
				index++;
			});

			// check if we should add the questionmark
			var addition = (serialized === '') ? '' : '?';
			var anchor = (getUrlObj.anchor) ? '#' + getUrlObj.anchor : '';

			uri = getUrlObj.protocol + '://' + getUrlObj.authority + getUrlObj.directory + getUrlObj.file + addition + serialized + anchor;

			return uri;
		}

	};

	// autoinits
	CMS.API.Helpers.preventSubmit();

});
})(CMS.$);
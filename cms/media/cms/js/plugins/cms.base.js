/**
 * @author:		Angelo Dini
 * @copyright:	http://www.divio.ch under the BSD Licence
 * @requires:	Classy, jQuery
 *
 * assign Class and CMS namespace */
 var CMS = CMS || {};

/*##################################################|*/
/* #CUSTOM APP# */
jQuery(document).ready(function ($) {
	/**
	 * Security
	 * @version: 0.1.1
	 * @description: Adds security layer to CMS namespace
	 * @public_methods:
	 *	- CMS.Security.csrf();
	 */
	CMS.Security = {
	
		csrf: function () {
			$.ajaxSetup({
				beforeSend: function (xhr, settings) {
					// get cookies without jquery.cookie.js
					function getCookie(name) {
						var cookieValue = null;
						if(document.cookie && (document.cookie != '')) {
							var cookies = document.cookie.split(';');
							for (var i = 0; i < cookies.length; i++) {
								var cookie = $.trim(cookies[i]);
								// Does this cookie string begin with the name we want?
								if (cookie.substring(0, name.length + 1) == (name + '=')) {
									cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
									break;
								}
							}
						}
						return cookieValue;
					}
					// do some url checks
					var base_doc_url = document.URL.match(/^http[s]{0,1}:\/\/[^\/]+\//)[0];
					var base_settings_url = settings.url.match(/^http[s]{0,1}:\/\/[^\/]+\//);
					if(base_settings_url != null) {
						base_settings_url = base_settings_url[0];
					}
					if(!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url)) || base_doc_url == base_settings_url) {
						// Only send the token to relative URLs i.e. locally.
						xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
					}
				}
			});
		}
	
	};
	
	/**
	 * Helpers
	 * @version: 0.1.1
	 * @description: Adds helper methods to be invoked
	 * @public_methods:
	 *	- CMS.Helpers.reloadBrowser();
	 *	- CMS.Helpers.getUrl(str);
	 *	- CMS.Helpers.setUrl(getUrlObj, addParam, removeParam);
	 */
	CMS.Helpers = {
	
		reloadBrowser: function () {
			window.location.reload();
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

		setUrl: function (getUrlObj, addParam, removeParam) {
			var query = getUrlObj.queryKey;
			var serialized = '';
			var index = 0;

			// we could loop the query and replace the param at the right place
			// but instead of replacing it just append it to the end of the query so its more visible
			delete query[removeParam];
				   query[addParam] = '';

			$.each(query, function (key, value) {
				// add &
				if(index != 0) serialized += '&';
				// if a value is given attach it
				serialized += (value) ? (key + '=' + value) : (key);
				index++;
			});

			uri = getUrlObj.directory + '?' + serialized;

			return uri;
		}
	
	};

});
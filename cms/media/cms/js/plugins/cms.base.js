/**
 * @author:		Angelo Dini
 * @copyright:	http://www.divio.ch under the BSD Licence
 * @requires:	Classy, jQuery
 *
 * assign Class and CMS namespace */
 var CMS = CMS || {};
     CMS.Class = CMS.Class || Class.$noConflict();

(function ($) {
/*##################################################|*/
/* #CMS.BASE# */
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
	 * @version: 0.1.0
	 * @description: Adds helper methods to be invoked
	 * @public_methods:
	 *	- CMS.Helpers.reloadBrowser();
	 *	- CMS.Helpers.insertUrl(url, name, value);
	 *	- CMS.Helpers.removeUrl(url, name);
	 */
	CMS.Helpers = {
	
		reloadBrowser: function () {
			window.location.reload();
		},
		
		insertUrl: function (url, name, value) {
			// this is a one to one copy from the old toolbar
			if(url.substr(url.length-1, url.length)== "&") url = url.substr(0, url.length-1); 
			var dash_splits = url.split("#");
			url = dash_splits[0];
			var splits = url.split(name + "=");
			if(splits.length == 1) splits = url.split(name);
			var get_args = false;
			if(url.split("?").length>1) get_args = true;
			if(splits.length > 1){
				var after = "";
				if(splits[1].split("&").length > 1) after = splits[1].split("&")[1];
				url = splits[0] + name;
				if(value) url += "=" + value;
				url += "&" + after;
			} else {
				if(get_args) { url = url + "&" + name; } else { url = url + "?" + name; }
				if(value) url += "=" + value;
			}
			if(dash_splits.length>1) url += '#' + dash_splits[1];
			if(url.substr(url.length-1, url.length)== "&") url = url.substr(0, url.length-1);
			
			return url;
		},
		
		removeUrl: function (url, name) {
			// this is a one to one copy from the old toolbar
			var dash_splits = url.split("#");
			url = dash_splits[0];
			var splits = url.split(name + "=");
			if(splits.length == 1) splits = url.split(name);
			if(splits.length > 1){
				var after = "";
				if (splits[1].split("&").length > 1) after = splits[1].split("&")[1];
				if (splits[0].substr(splits[0].length-2, splits[0].length-1)=="?" || !after) {
					url = splits[0] + after;
				} else {
					url = splits[0] + "&" + after;
				}
			}
			if(url.substr(url.length-1,1) == "?") url = url.substr(0, url.length-1);
			if(dash_splits.length > 1 && dash_splits[1]) url += "#" + dash_splits[1];
			
			return url;
		}
	
	};

});

})(jQuery);
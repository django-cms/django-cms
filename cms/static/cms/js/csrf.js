// TODO: This file is intended to be deprecated as soon as the jQuery version
// in the admin is fixed
// TODO: Indentation is broken in this file.

(function($){

$.ajaxSetup({
				beforeSend: function (xhr, settings) {
					if (typeof(settings.csrfTokenSet) != undefined && settings.csrfTokenSet) {
						// CSRF token has already been set elsewhere so we won't touch it.
						return true;
					}
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
						settings.csrfTokenSet = true;
					}
				}
			});
			return 'ready';












$.fn.cmsPatchCSRF = function () {
$.ajaxSetup({
beforeSend: function(xhr, settings) {
if (typeof(settings.csrfTokenSet) !== undefined && settings.csrfTokenSet) {
    // CSRF token has already been set elsewhere so we won't touch it.
    return true;
} 
function getCookie(name) {
var cookieValue = null;
if (document.cookie && document.cookie != '') {
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
var base_doc_url = document.URL.match(/^http[s]{0,1}:\/\/[^\/]+\//)[0];
var base_settings_url = settings.url.match(/^http[s]{0,1}:\/\/[^\/]+\//);
if (base_settings_url != null) {
base_settings_url = base_settings_url[0];
}
if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url)) || base_doc_url == base_settings_url) {
// Only send the token to relative URLs i.e. locally.
xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
settings.csrfTokenSet = true;
}
}
});
};
})(jQuery);

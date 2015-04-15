/*##################################################|*/
/* #CMS# */

// ensuring django namespace is set correctly
window.django = window.django || undefined;

// ensuring jQuery namespace is set correctly
window.jQuery = (django && django.jQuery) ? django.jQuery : window.jQuery || undefined;

// ensuring Class namespace is set correctly
window.Class = window.Class || undefined;

// ensuring CMS namespace is set correctly
var CMS = {
	'$': (typeof jQuery === 'function') ? jQuery : undefined,
	'Class': (typeof Class === 'function') ? Class : undefined,
	'API': {}
};

/*##################################################|*/
/* #CMS.API# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * CNS.API.Helpers
	 * Multiple helpers used accross all CMS features
	 */
	CMS.API.Helpers = {

		// redirects to a specific url or reloads browser
		reloadBrowser: function (url, timeout, ajax) {
			var that = this;
			// is there a parent window?
			var parent = (window.parent) ? window.parent : window;

			// if there is an ajax reload, prioritize
			if(ajax) {
				parent.CMS.API.locked = true;
				// check if the url has changed, if true redirect to the new path
				// this requires an ajax request
				$.ajax({
					'async': false,
					'type': 'GET',
					'url': parent.CMS.config.request.url,
					'data': {
						'model': parent.CMS.config.request.model,
						'pk': parent.CMS.config.request.pk
					},
					'success': function (response) {
						parent.CMS.API.locked = false;

						if(response === '' && !url) {
							// cancel if response is empty
							return false;
						} else if(parent.location.pathname !== response) {
							// api call to the backend to check if the current path is still the same
							that.reloadBrowser(response);
						} else if(url === 'REFRESH_PAGE') {
							// if on_close provides REFRESH_PAGE, only do a reload
							that.reloadBrowser();
						} else if(url) {
							// on_close can also provide a url, reload to the new destination
							that.reloadBrowser(url);
						}
					}
				});

				// cancel further operations
				return false;
			}

			// add timeout if provided
			parent.setTimeout(function () {
				if (url && url != parent.location.href) {
					// location.reload() takes precedence over this, so we
					// don't want to reload the page if we need a redirect
					parent.location.href = url;
				}
				else {
					// ensure page is always reloaded #3413
					parent.location.reload()
				}
			}, timeout || 0);
		},

		// disable multiple form submissions
		preventSubmit: function () {
			var forms = $('#cms_toolbar').find('form');
				forms.submit(function () {
					// show loader
					CMS.API.Toolbar._loader(true);
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
		},

		// handles the tooltip for the plugins
		showTooltip: function (name, id) {
			var tooltip = $('.cms_tooltip');

			// change css and attributes
			tooltip.css('visibility', 'visible')
				.data('plugin_id', id || null)
				.show()
				.find('span').html(name);

			// attaches move event
			// this sets the correct position for the edit tooltip
			$('body').bind('mousemove.cms', function (e) {
				// so lets figure out where we are
				var offset = 20;
				var relX = e.pageX - $(tooltip).offsetParent().offset().left;
				var relY = e.pageY - $(tooltip).offsetParent().offset().top;
				var bound = $(tooltip).offsetParent().width();
				var pos = relX + tooltip.outerWidth(true) + offset;

				tooltip.css({
					'left': (pos >= bound) ? relX - tooltip.outerWidth(true) - offset : relX + offset,
					'top': relY - 12
				});
			});

			// attach tooltip event for touch devices
			tooltip.bind('touchstart.cms', function () {
				$('.cms_plugin-' + $(this).data('plugin_id')).trigger('dblclick');
			});
		},

		hideTooltip: function () {
			var tooltip = $('.cms_tooltip');

			// change css
			tooltip.css('visibility', 'hidden').hide();

			// unbind events
			$('body').unbind('mousemove.cms');
			tooltip.unbind('touchstart.cms');
		},

		// sends or retrieves a JSON from localStorage or the session if local storage is not available
		setSettings: function (settings) {
			var that = this;
			// merge settings
			settings = JSON.stringify($.extend({}, CMS.config.settings, settings));
			// set loader
			if(CMS.API.Toolbar) CMS.API.Toolbar._loader(true);

			// use local storage or session
			if(window.localStorage) {
				// save within local storage
				localStorage.setItem('cms_cookie', settings);
				if(CMS.API.Toolbar) CMS.API.Toolbar._loader(false);
			} else {
				// save within session
				CMS.API.locked = true;

				$.ajax({
					'async': false,
					'type': 'POST',
					'url': CMS.config.urls.settings,
					'data': {
						'csrfmiddlewaretoken': this.config.csrf,
						'settings': settings
					},
					'success': function (data) {
						CMS.API.locked = false;
						// determine if logged in or not
						settings = (data) ? JSON.parse(data) : CMS.config.settings;
						if(CMS.API.Toolbar) CMS.API.Toolbar._loader(false);
					},
					'error': function (jqXHR) {
						that.showError(jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText);
					}
				});
			}

			// save settings
			CMS.settings = JSON.parse(settings);

			// ensure new settings are returned
			return CMS.settings;
		},

		getSettings: function () {
			var that = this;
			var settings;
			// set loader
			if(CMS.API.Toolbar) CMS.API.Toolbar._loader(true);

			// use local storage or session
			if(window.localStorage) {
				// get from local storage
				settings = JSON.parse(localStorage.getItem('cms_cookie'));
				if(CMS.API.Toolbar) CMS.API.Toolbar._loader(false);
			} else {
				CMS.API.locked = true;
				// get from session
				$.ajax({
					'async': false,
					'type': 'GET',
					'url': CMS.config.urls.settings,
					'success': function (data) {
						CMS.API.locked = false;
						// determine if logged in or not
						settings = (data) ? JSON.parse(data) : CMS.config.settings;
						if(CMS.API.Toolbar) CMS.API.Toolbar._loader(false);
					},
					'error': function (jqXHR) {
						that.showError(jqXHR.response + ' | ' + jqXHR.status + ' ' + jqXHR.statusText);
					}
				});
			}

			if(settings === null) settings = this.setSettings(CMS.config.settings);

			// save settings
			CMS.settings = settings;

			// ensure new settings are returned
			return CMS.settings;
		},

		// prevents scrolling when another scrollbar is used (for better ux)
		preventScroll: function (disable) {
			// TODO: currently disabled
/*
			// cancel if scrollbar is not visible
			if($(document).height() <= $(window).height()) return false;

			var scrollTop = $(window).scrollTop();
			var html = $('html');

			if(disable) {
				html.addClass('cms_toolbar-noscroll').css('top',-scrollTop).data('scroll', scrollTop);
			} else {
				html.removeClass('cms_toolbar-noscroll');
				$(window).scrollTop(html.data('scroll'));
			}
*/
		}

	};

	// autoinits
	CMS.API.Helpers.preventSubmit();

});
})(CMS.$);
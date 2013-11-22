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
	 * Multiple helpers used accross all CMS features
	 */
	CMS.API.Helpers = {

		// redirects to a specific url or reloads browser
		reloadBrowser: function (url, timeout) {
			// is there a parent window?
			var parent = (window.parent) ? window.parent : window;
			// add timeout if provided
			parent.setTimeout(function () {
				(url) ? parent.location.href = url : parent.location.reload();
			}, timeout || 0);
		},

		// disable multiple form submissions
		preventSubmit: function () {
			var forms = $('#cms_toolbar').find('form');
			forms.submit(function () {
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
			var tooltip = $('.cms_placeholders-tooltip');

			// change css and attributes
			tooltip.css('visibility', 'visible')
				.data('plugin_id', id)
				.show()
				.find('span').html(name);

			// attaches move event
			// this sets the correct position for the edit tooltip
			$('body').bind('mousemove.cms', function (e) {
				// so lets figure out where we are
				var offset = 20;
				var bound = $(document).width();
				var pos = e.pageX + tooltip.outerWidth(true) + offset;

				tooltip.css({
					'left': (pos >= bound) ? e.pageX - tooltip.outerWidth(true) - offset : e.pageX + offset,
					'top': e.pageY - 12
				});
			});

			// attach tooltip event for touch devices
			tooltip.bind('touchstart.cms', function () {
				$('#cms_plugin-' + $(this).data('plugin_id')).trigger('dblclick');
			});
		},

		hideTooltip: function () {
			var tooltip = $('.cms_placeholders-tooltip');

			// change css
			tooltip.css('visibility', 'hidden').hide();

			// unbind events
			$('body').unbind('mousemove.cms');
			tooltip.unbind('touchstart.cms');
		},

		// sends or retrieves a JSON from localStorage or the session if local storage is not available
		setSettings: function (settings) {
			// cancel if local storage is not available
			if(!window.localStorage) return false;

			// set settings
			settings = $.extend({}, CMS.config.settings, settings);
			// save inside local storage
			localStorage.setItem('cms_cookie', JSON.stringify(settings));
		},

		getSettings: function () {
			// cancel if local storage is not available
			if(!window.localStorage) return false;

			// check if there are settings defined
			var settings = localStorage.getItem('cms_cookie');

			// set settings are not defined, ensure they are
			if(settings === null) this.setSettings(CMS.config.settings);

			// finally get settings
			return JSON.parse(localStorage.getItem('cms_cookie'));
		},

		// prevents scrolling when another scrollbar is used (for better ux)
		preventScroll: function (disable) {
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
		}

	};

	// autoinits
	CMS.API.Helpers.preventSubmit();

});
})(CMS.$);

// this will be fixed in jQuery 1.6+
(function ( $ ) {
    var filters = $.expr[":"];
    if ( !filters.focus ) {
        filters.focus = function( elem ) {
           return elem === document.activeElement && ( elem.type || elem.href );
        };
    }
})( jQuery );
/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Clipboard
	 * Handles copy & paste
	 */
	CMS.Clipboard = new CMS.Class({

		implement: [CMS.API.Helpers],

		options: {
			'position': 220, // offset to top
			'speed': 100,
			'id': null,
			'url': ''
		},

		initialize: function (options) {
			this.clipboard = $('.cms_clipboard');
			this.options = $.extend(true, {}, this.options, options);
			this.config = CMS.config;
			this.settings = CMS.settings;

			// elements
			this.containers = this.clipboard.find('.cms_clipboard-containers > .cms_draggable');
			this.triggers = this.clipboard.find('.cms_clipboard-triggers a');
			this.triggerRemove = this.clipboard.find('.cms_clipboard-empty a');

			// states
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'touchend.cms';
			this.timer = function () {};

			// setup initial stuff
			this._setup();

			// setup events
			this._events();
		},

		// initial methods
		_setup: function () {
			var that = this;

			// attach visual events
			this.triggers.bind('mouseenter mouseleave', function (e) {
				e.preventDefault();
				// clear timeout
				clearTimeout(that.timer);

				if(e.type === 'mouseleave' && !that.containers.has(e.toElement).length) hide();

				var index = that.clipboard.find('.cms_clipboard-triggers a').index(this);
				var el = that.containers.eq(index);
				// cancel if element is already open
				if(el.data('open') === true) return false;

				// show element
				that.containers.stop().css({ 'margin-left': -that.options.position }).data('open', false);
				el.stop().animate({ 'margin-left': 0 }, that.options.speed);
				el.data('open', true);
			});
			that.containers.bind('mouseover mouseleave', function (e) {
				// clear timeout
				clearTimeout(that.timer);

				// cancel if we trigger mouseover
				if(e.type === 'mouseover') return false;

				// we need a little timer to detect if we should hide the menu
				hide();
			});

			function hide() {
				that.timer = setTimeout(function () {
					that.containers.stop().css({ 'margin-left': -that.options.position }).data('open', false);
				}, that.options.speed);
			}
		},

		_events: function () {
			var that = this;

			// add remove event
			this.triggerRemove.bind(this.click, function (e) {
				e.preventDefault();
				that.clear(function () {
				    // remove element on success
				    that.clipboard.hide();
				});
			});
		},

		// public methods
		clear: function (callback) {
			// post needs to be a string, it will be converted using JSON.parse
			var post = '{ "csrfmiddlewaretoken": "' + this.config.csrf + '" }';
			// redirect to ajax
			CMS.API.Toolbar.openAjax(this.config.clipboard.url, post, '', callback);
		}

	});

});
})(CMS.$);
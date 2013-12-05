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
			'speed': 100
		},

		initialize: function (options) {
			this.options = $.extend(true, {}, this.options, options);

			// elements
			this.clipboard = $('.cms_clipboard');
			this.triggerRemove = this.clipboard.find('.cms_clipboard-empty a');
			this.triggers = this.clipboard.find('.cms_clipboard-triggers a');
			this.containers = this.clipboard.find('.cms_clipboard-containers > .cms_draggable');

			// states
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'touchend.cms';
			this.timer = function () {};

			// setup initial stuff
			this._setup();

			// setup events
			this._events();
		},

		// private methods
		_setup: function () {
			// nothing here yet
		},

		_events: function () {
			var that = this;

			// add remove event
			this.triggerRemove.bind(this.click, function (e) {
				e.preventDefault();
				CMS.API.Toolbar.openAjax($(this).attr('href'), $(this).attr('data-post'));
			});

			// add animation events
			this.triggers.bind('mouseenter mouseleave', function (e) {
				e.preventDefault();
				// clear timeout
				clearTimeout(that.timer);

				if(e.type === 'mouseleave') hide();

				that.triggers = that.clipboard.find('.cms_clipboard-triggers a');
				that.containers = that.clipboard.find('.cms_clipboard-containers > .cms_draggable');
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

		// TODO from stop on drag & drop
		_update: function () {
			// cancel if there is no clipboard available
			if(!this.clipboard.length) return false;

			var containers = this.clipboard.find('.cms_clipboard-containers .cms_draggable');
			var triggers = this.clipboard.find('.cms_clipboard-triggers .cms_clipboard-numbers');

			var lengthContainers = containers.length;
			var lengthTriggers = triggers.length;

			// only proceed if the items are not in sync
			if(lengthContainers === lengthTriggers) return false;

			// set visible elements
			triggers.hide();
			for(var i = 0; i < lengthContainers; i++) {
				triggers.eq(i).show();
			}

			// remove clipboard if empty
			if(lengthContainers <= 0) this.clipboard.remove();
		}

	});

});
})(CMS.$);
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

		options: {},

		initialize: function (options) {
			this.options = $.extend(true, {}, this.options, options);
			this.clipboard = $('.cms_clipboard');

			// helpers
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'touchend.cms';

			this._setup();
		},

		// private methods
		_setup: function () {
			var that = this;
			var remove = this.clipboard.find('.cms_clipboard-empty a');
			var triggers = this.clipboard.find('.cms_clipboard-triggers a');
			var containers = this.clipboard.find('.cms_clipboard-containers > .cms_draggable');
			var position = 220;
			var speed = 100;
			var timer = function () {};

			// add remove event
			remove.bind(this.click, function (e) {
				e.preventDefault();
				CMS.API.Toolbar.openAjax($(this).attr('href'), $(this).attr('data-post'));
			});

			// add animation events
			triggers.bind('mouseenter mouseleave', function (e) {
				e.preventDefault();
				// clear timeout
				clearTimeout(timer);

				if(e.type === 'mouseleave') hide();

				triggers = that.clipboard.find('.cms_clipboard-triggers a');
				containers = that.clipboard.find('.cms_clipboard-containers > .cms_draggable');
				var index = that.clipboard.find('.cms_clipboard-triggers a').index(this);
				var el = containers.eq(index);
				// cancel if element is already open
				if(el.data('open') === true) return false;

				// show element
				containers.stop().css({ 'margin-left': -position }).data('open', false);
				el.stop().animate({ 'margin-left': 0 }, speed);
				el.data('open', true);
			});
			containers.bind('mouseover mouseleave', function (e) {
				// clear timeout
				clearTimeout(timer);

				// cancel if we trigger mouseover
				if(e.type === 'mouseover') return false;

				// we need a little timer to detect if we should hide the menu
				hide();
			});

			function hide() {
				timer = setTimeout(function () {
					containers.stop().css({ 'margin-left': -position }).data('open', false);
				}, speed);
			}
		},

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
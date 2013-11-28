/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * StructureBoard
	 * handles drag & drop, mode switching and
	 */
	CMS.StructureBoard = new CMS.Class({

		implement: [CMS.API.Helpers],

		options: {
			'speed': 300
		},

		initialize: function (options) {
			this.container = $('.cms_structure');
			this.options = $.extend(true, {}, this.options, options);
			this.config = CMS.config;
			this.settings = this.getSettings();

			// elements
			this.toolbar = $('#cms_toolbar');
			this.sortables = $('.cms_draggables'); // use global scope
			this.plugins = $('.cms_plugin');
			this.placeholders = $('.cms_placeholder');
			this.dragitems = $('.cms_draggable');
			this.dropareas = $('.cms_droppable');

			// states
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'tap.cms';
			this.timer = function () {};
			this.state = false;
			this.dragging = false;

			// setup initial stuff
			this._setup();

			// setup events
			this._events();
		},

		_setup: function () {
			var that = this;

			// setup toolbar mode
			if(this.settings.mode === 'structure') setTimeout(function () { that.show(); }, 100);

			// check if modes should be visible
			if(this.placeholders.length) {
				this.toolbar.find('.cms_toolbar-item-cms-mode-switcher').show();
			}

			// add drag & drop functionality
			this._drag();
			// prevent click events to detect double click
			this._preventEvents();
		},

		_events: function () {
			var that = this;
			var modes = this.toolbar.find('.cms_toolbar-item-cms-mode-switcher a');

			// show edit mode
			modes.eq(0).bind(this.click, function (e) {
				e.preventDefault();
				// cancel if already active
				if(that.settings.mode === 'edit') return false;
				// otherwise hide
				that.hide();
			});
			// show structure mode
			modes.eq(1).bind(this.click, function (e) {
				e.preventDefault();
				// cancel if already active
				if(that.settings.mode === 'structure') return false;
				// otherwise show
				that.show();
			});

			// keyboard handling
			$(document).bind('keydown', function (e) {
				// check if we have an important focus
				var fields = $('*:focus');
				// 32 = space
				if(e.keyCode === 32 && that.settings.mode === 'structure' && !fields.length) {
					e.preventDefault();
					that.hide();
				} else if(e.keyCode === 32 && that.settings.mode === 'edit' && !fields.length) {
					e.preventDefault();
					that.show();
				}
			});
		},

		// public methods
		show: function () {
			// set active item
			var modes = this.toolbar.find('.cms_toolbar-item-cms-mode-switcher a');
				modes.removeClass('cms_btn-active').eq(1).addClass('cms_btn-active');

			// show clipboard in structure mode
			this.container.find('.cms_clipboard').fadeIn(this.options.speed);

			// apply new settings
			this.settings.mode = 'structure';
			this.setSettings(this.settings);

			// show canvas
			this._showBoard();
		},

		hide: function () {
			// set active item
			var modes = this.toolbar.find('.cms_toolbar-item-cms-mode-switcher a');
				modes.removeClass('cms_btn-active').eq(0).addClass('cms_btn-active');

			// hide clipboard if in edit mode
			this.container.find('.cms_clipboard').hide();

			this.settings.mode = 'edit';
			this.setSettings(this.settings);

			// hide canvas
			this._hideBoard();
		},

		getId: function (el) {
			// cancel if no element is defined
			if(el === undefined || el === null || el.length <= 0) return false;

			var id = null;

			if(el.hasClass('cms_plugin')) {
				id = el.attr('class').replace('cms_plugin cms_plugin-', '');
			} else if(el.hasClass('cms_draggable')) {
				id = el.attr('class').replace('cms_draggable cms_draggable-', '');
			} else {
				id = el.attr('class').replace('cms_placeholder cms_placeholder-', '');
			}

			return id;
		},

		getIds: function (els) {
			var that = this;
			var array = [];
			els.each(function () {
				array.push(that.getId($(this)));
			});
			return array;
		},

		setActive: function (id) {
			// reset active statesdragholders
			this.dragitems.removeClass('cms_draggable-selected');
			this.plugins.removeClass('cms_plugin-active');

			// if false is provided, only remove classes
			if(id === false) return false;

			// attach active class to current element
			var dragitem = $('.cms_draggable-' + id);
			var plugin = $('.cms_plugin-' + id);

			// collapse all previous elements
			var collapsed = dragitem.parentsUntil('.cms_dragarea').siblings().not('.cms_dragitem-expanded');
				collapsed.trigger(this.click);

			// set new classes
			dragitem.addClass('cms_draggable-selected');
			plugin.addClass('cms_plugin-active');
		},

		// private methods
		_showBoard: function () {
			var body = $('body');

			// apply correct width and height to the structure container
			var width = $(window).width();
			var height = $(window).height();
			var toolbarHeight = this.toolbar.find('.cms_toolbar').height();
			// determine if we should use body width or height
			if(width <= body.width()) width = body.width();
			if(height <= body.height()) height = body.height();

			this.container.css({
				'top': (this.settings.toolbar === 'collapsed') ? 0 : toolbarHeight,
				'width': width,
				'height': height
			});

			this.container.stop(true, true).fadeIn(this.options.speed);

			// TODO this is gonna be funny
			// loop over all placeholders
			var id = null;
			var area = null;

			// start calculating
			this.plugins.hide();
			this.placeholders.show();
			this.placeholders.each(function (index, item) {
				item = $(item);
				id = item.data('settings').placeholder_id;
				area = $('.cms_dragarea-' + id);
				// to calculate the correct offset, we need to set the
				// placeholders correct heights and than set the according position
				item.height(area.outerHeight(true));
				area.css({
					'top': item.offset().top,
					'left': item.offset().left,
					'width': item.width()
				});
			});
			// reset calculating
			this.placeholders.height(0);
			this.plugins.show();
		},

		_hideBoard: function () {
			this.container.stop(true, true).fadeOut(this.options.speed / 2);
		},

		_drag: function () {
			var that = this;
			var dropped = false;
			var droparea = null;
			var dropzone = null;

			this.sortables.nestedSortable({
				'items': '.cms_draggable',
				'handle': '.cms_dragitem',
				'placeholder': 'cms_droppable',
				'connectWith': this.sortables,
				'tolerance': 'pointer',
				'toleranceElement': '> div',
				'dropOnEmpty': true,
				'forcePlaceholderSize': true,
				'helper': 'clone',
				'appendTo': 'body',
				'cursor': 'move',
				'opacity': 0.4,
				'zIndex': 999999,
				'delay': 100,
				'refreshPositions': true,
				// nestedSortable
				'listType': 'div.cms_draggables',
				'doNotClear': true,
				'disableNestingClass': 'cms_draggable-disabled',
				'errorClass': 'cms_draggable-disallowed',
				'hoveringClass': 'cms_draggable-hover',
				// methods
				'start': function (e, ui) {
					that.dragging = true;
					// show empty
					$('.cms_dragbar-empty-wrapper').show();
					// ensure all menus are closed
					$('.cms_dragitem .cms_submenu').hide();
					// remove classes from empty dropzones
					$('.cms_dragbar-empty').removeClass('cms_draggable-disallowed');
					// fixes placeholder height
					ui.placeholder.height(ui.item.height());
					// show placeholder without entries
					$('.cms_draggables').each(function () {
						if($(this).children().length === 0) {
							$(this).show();
						}
					});
				},

				'stop': function (event, ui) {
					that.dragging = false;
					// hide empty
					$('.cms_dragbar-empty-wrapper').hide();

					// cancel if isAllowed returns false
					if(!that.state) return false;

					// handle dropped event
					if(dropped) {
						droparea.prepend(ui.item);
						dropped = false;
					}

					// we pass the id to the updater which checks within the backend the correct place
					var id = ui.item.attr('id').replace('cms_draggable-', '');
					var plugin = $('.cms_plugin-' + id);
						plugin.trigger('cms.placeholder.update');

					// update clipboard entries
					CMS.API.Clipboard._update(ui.item);

					// reset placeholder without entries
					$('.cms_draggables').each(function () {
						if($(this).children().length === 0) {
							$(this).hide();
						}
					});
				},
				'isAllowed': function(placeholder, placeholderParent, originalItem) {
					// getting restriction array
					var bounds = [];
					// save original state events
					var original = $('.cms_plugin-' + that.getId(originalItem));
					// cancel if item has no settings
					if(original.data('settings') === undefined) return false;
					var type = original.data('settings').plugin_type;
					// prepare variables for bound
					var holder = placeholder.parent().prevAll('.cms_placeholder-bar').first();
					var plugin = $('.cms_plugin-' + that.getId(placeholder.closest('.cms_draggable')));

					// now set the correct bounds
					if(dropzone) bounds = dropzone.data('settings').plugin_restriction;
					if(plugin.length) bounds = plugin.data('settings').plugin_restriction;
					if(holder.length) bounds = holder.data('settings').plugin_restriction;

					// if restrictions is still empty, proceed
					that.state = (bounds.length <= 0 || $.inArray(type, bounds) !== -1) ? true : false;

					return that.state;
				}
			});

			// attach escape event to cancel dragging
			$(document).bind('keyup.cms', function(e, cancel){
				if(e.keyCode === 27 || cancel) {
					that.state = false;
					that.sortables.sortable('cancel');
				}
			});

			// define droppable helpers
			this.dropareas.droppable({
				'greedy': true,
				'accept': '.cms_draggable',
				'tolerance': 'pointer',
				'activeClass': 'cms_draggable-allowed',
				'hoverClass': 'cms_draggable-hover-allowed',
				'over': function (event) {
					dropzone = $(event.target).parent().prev();
					if(!that.state) $(event.target).addClass('cms_draggable-disallowed');
				},
				'out': function (event) {
					dropzone = null;
					$(event.target).removeClass('cms_draggable-disallowed');
				},
				'drop': function (event) {
					dropped = true;
					droparea = $(event.target).parent().nextAll('.cms_draggables').first();
				}
			});
		},

		_preventEvents: function () {
			var clicks = 0;
			var delay = 500;
			var timer = function () {};

			// unbind click event if already initialized
			this.plugins.find('a').bind(this.click, function (e) {
				e.preventDefault();

				// increment
				clicks++;

				// single click
				if(clicks === 1) {
					timer = setTimeout(function () {
						clicks = 0;
						// cancel if link contains a hash
						if($(e.currentTarget).attr('href').indexOf('#') === 0) return false;
						// we need to redirect to the default behaviours
						// all events will be lost in edit mode, use '#' if href should not be triggered
						window.location.href = $(e.currentTarget).attr('href');
					}, delay);
				}

				// double click
				if(clicks === 2) {
					clearTimeout(timer);
					clicks = 0;
				}
			});
		}

	});

});
})(CMS.$);
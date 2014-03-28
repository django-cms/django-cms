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
			this.settings = CMS.settings;

			// elements
			this.toolbar = $('#cms_toolbar');
			this.sortables = $('.cms_draggables'); // use global scope
			this.plugins = $('.cms_plugin');
			this.render_model = $('.cms_render_model');
			this.placeholders = $('.cms_placeholder');
			this.dragitems = $('.cms_draggable');
			this.dragareas = $('.cms_dragarea');
			this.dropareas = $('.cms_droppable');
			this.dimmer = this.container.find('.cms_structure-dimmer');
			this.clipboard = $('.cms_clipboard');

			// states
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'tap.cms';
			this.timer = function () {};
			this.interval = function () {};
			this.state = false;
			this.dragging = false;

			// setup initial stuff
			this._setup();

			// setup events
			this._events();
		},

		// initial methods
		_setup: function () {
			var that = this;

			// cancel if there are no dragareas
			if(!this.dragareas.length) return false;

			// setup toolbar mode
			if(this.settings.mode === 'structure') setTimeout(function () { that.show(true); }, 100);

			// check if modes should be visible
			if(this.placeholders.length) {
				this.toolbar.find('.cms_toolbar-item-cms-mode-switcher').show();
			}

			// add drag & drop functionality
			this._drag();
			// prevent click events to detect double click
			this.preventEvents(this.plugins);
		},

		_events: function () {
			var that = this;
			var modes = this.toolbar.find('.cms_toolbar-item-cms-mode-switcher a');

			// show edit mode
			modes.eq(1).bind(this.click, function (e) {
				e.preventDefault();
				// cancel if already active
				if(that.settings.mode === 'edit') return false;
				// otherwise hide
				that.hide();
			});
			// show structure mode
			modes.eq(0).bind(this.click, function (e) {
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
		show: function (init) {
			// cancel show if live modus is active
			if(CMS.config.mode === 'live') return false;

			// set active item
			var modes = this.toolbar.find('.cms_toolbar-item-cms-mode-switcher a');
				modes.removeClass('cms_btn-active').eq(0).addClass('cms_btn-active');

			// show clipboard
			this.clipboard.css('opacity', 1).fadeIn(this.options.speed);

			// apply new settings
			this.settings.mode = 'structure';
			if(!init) this.settings = this.setSettings(this.settings);

			// ensure all elements are visible
			this.dragareas.show();

			// show canvas
			this._showBoard();
		},

		hide: function (init) {
			// cancel show if live modus is active
			if(CMS.config.mode === 'live') return false;

			// set active item
			var modes = this.toolbar.find('.cms_toolbar-item-cms-mode-switcher a');
				modes.removeClass('cms_btn-active').eq(1).addClass('cms_btn-active');

			// hide clipboard if in edit mode
			this.container.find('.cms_clipboard').hide();

			// hide clipboard
			this.clipboard.hide();

			this.settings.mode = 'edit';
			if(!init) this.settings = this.setSettings(this.settings);

			// hide canvas
			this._hideBoard();
		},

		getId: function (el) {
			// cancel if no element is defined
			if(el === undefined || el === null || el.length <= 0) return false;

			var id = null;
			var cls = el.attr('class').split(' ')[1];

			if(el.hasClass('cms_plugin')) {
				id = cls.replace('cms_plugin-', '');
			} else if(el.hasClass('cms_draggable')) {
				id = cls.replace('cms_draggable-', '');
			} else if(el.hasClass('cms_placeholder')) {
				id = cls.replace('cms_placeholder-', '');
			} else if(el.hasClass('cms_dragbar')) {
				id = cls.replace('cms_dragbar-', '');
			} else if(el.hasClass('cms_dragarea')) {
				id = cls.replace('cms_dragarea-', '');
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

		setActive: function (id, state) {
			var that = this;
			// resets
			this.dragitems.removeClass('cms_draggable-selected');
			this.plugins.removeClass('cms_plugin-active');
			this.dragitems.unbind('mousedown.cms.longclick');

			// only reset if no id is provided
			if(id === false) return false;

			// attach active class to current element
			var dragitem = $('.cms_draggable-' + id);
			var plugin = $('.cms_plugin-' + id);

			// if we switch from content to edit, show only a single plcaeholder
			if(state) {
				// quick show
				this._showBoard();

				// show clipboard
				this.clipboard.show().css('opacity', 0.2);

				// prevent default visibility
				this.dragareas.css('opacity', 0.2);

				// show single placeholder
				dragitem.closest('.cms_dragarea').show().css('opacity', 1);

				// attach event to switch to fullmode when dragging
				this.dragitems.bind('mousedown.cms.longclick', function () {
					that.show();
					that.setActive(false);
				});

			// otherwise hide and reset the board
			} else {
				this.hide();
			}

			// collapse all previous elements
			var collapsed = dragitem.parentsUntil('.cms_dragarea').siblings().not('.cms_dragitem-expanded');
				collapsed.trigger(this.click);

			// set new classes
			dragitem.addClass('cms_draggable-selected');
			plugin.addClass('cms_plugin-active');
		},

		preventEvents: function (elements) {
			var clicks = 0;
			var delay = 500;
			var timer = function () {};

			// unbind click event if already initialized
			elements.find('a').bind(this.click, function (e) {
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
		},

		// private methods
		_showBoard: function () {
			var that = this;
			var interval = 10;
			var timer = function () {};

			// show container
			this.container.show();
			this.dimmer.fadeIn(100);
			this.dragareas.css('opacity', 1);

			// add dimmer close
			this.dimmer.bind('mousedown mouseup', function (e) {
				// cancel on rightclick
				if(e.which === 3 || e.button === 2) return false;
				// proceed
				clearTimeout(timer);
				timer = setTimeout(function () {
					that.hide();
				}, 500);

				if(e.type === 'mouseup') clearTimeout(timer);
			});

			this.plugins.not(this.render_model).hide();
			this.placeholders.show();

			// attach event
			$(window).bind('resize.sideframe', function () {
				that._resizeBoard();
			}).trigger('resize.sideframe');

			// setup an interval
			this.interval = setInterval(function () {
				$(window).trigger('resize.sideframe');
			}, interval);
		},

		_hideBoard: function () {
			// hide elements
			this.container.hide();
			this.plugins.show();
			this.placeholders.hide();
			this.dimmer.hide();

			// detach event
			$(window).unbind('resize.sideframe');

			// clear interval
			clearInterval(this.interval);
		},

		_resizeBoard: function () {
			// calculate placeholder position
			var id = null;
			var area = null;
			var min = null;

			// start calculating
			this.placeholders.each(function (index, item) {
				item = $(item);
				id = item.data('settings').placeholder_id;
				area = $('.cms_dragarea-' + id);
				// to calculate the correct offset, we need to set the
				// placeholders correct heights and than set the according position
				item.height(area.outerHeight(true));
				// set min width
				min = (item.width()) ? 0 : 150;
				area.css({
					'top': item.offset().top - 5,
					'left': item.offset().left - min,
					'width': item.width() + min
				});
			});
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
				'zIndex': 9999999,
				'delay': 100,
				'refreshPositions': true,
				// nestedSortable
				'listType': 'div.cms_draggables',
				'doNotClear': true,
				//'disableNestingClass': 'cms_draggable-disabled',
				//'errorClass': 'cms_draggable-disallowed',
				//'hoveringClass': 'cms_draggable-hover',
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
					//var id = ui.item.attr('class').replace('cms_draggable cms_draggable-', '');
					var id = that.getId(ui.item);
					var plugin = $('.cms_plugin-' + id);

					// check if we copy/paste a plugin or not
					if(plugin.closest('.cms_clipboard').length) {
						plugin.trigger('cms.plugin.update');
					} else {
						plugin.trigger('cms.plugins.update');
					}

					// reset placeholder without entries
					$('.cms_draggables').each(function () {
						if($(this).children().length === 0) {
							$(this).hide();
						}
					});
				},
				'isAllowed': function(placeholder, placeholderParent, originalItem) {
					// cancel if action is excecuted
					if(CMS.API.locked) return false;
					// getting restriction array
					var bounds = [];
					// save original state events
					var original = $('.cms_plugin-' + that.getId(originalItem));
					// cancel if item has no settings
					if(original.length === 0 || original.data('settings') === null) return false;
					var type = original.data('settings').plugin_type;
					// prepare variables for bound
					var holderId = that.getId(placeholder.closest('.cms_dragarea'));
					var holder = $('.cms_placeholder-' + holderId);
					var plugin = $('.cms_plugin-' + that.getId(placeholder.closest('.cms_draggable')));

					// now set the correct bounds
					if(holder.length) bounds = holder.data('settings').plugin_restriction;
					if(plugin.length) bounds = plugin.data('settings').plugin_restriction;
					if(dropzone) bounds = dropzone.data('settings').plugin_restriction;

					// if parent has class disabled, dissalow drop
					if(placeholder.parent().hasClass('cms_draggable-disabled')) return false;

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
					dropzone = $('.cms_placeholder-' + that.getId($(event.target).parent().prev()));
					timer = setInterval(function () {
						// reset other empty placeholders
						$('.cms_dragbar-empty').removeClass('cms_draggable-disallowed');
						if(that.state) {
							$(event.target).removeClass('cms_draggable-disallowed');
						} else {
							$(event.target).addClass('cms_draggable-disallowed');
						}
					}, 10);
				},
				'out': function (event) {
					dropzone = null;
					$(event.target).removeClass('cms_draggable-disallowed');
					clearInterval(timer);
				},
				'drop': function (event) {
					dropped = true;
					droparea = $(event.target).parent().nextAll('.cms_draggables').first();
					clearInterval(timer);
				}
			});
		}

	});

});
})(CMS.$);
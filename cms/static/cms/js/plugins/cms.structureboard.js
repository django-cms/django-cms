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

		initialize: function (options) {
			this.options = $.extend(true, {}, this.options, options);

			this.plugins = $('.cms_plugin');
			this.toolbar = $('#cms_toolbar');
			this.sortables = $('.cms_draggables'); // use global scope
			this.dragging = false;
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'tap.cms';

			// this.dragitems = $('.cms_draggable');
			this.dropareas = $('.cms_droppable');

			this.timer = function () {};
			this.state = false;

			this._preventEvents();
			this._drag();
		},

		// public methods
		getId: function (el) {
			// cancel if no element is defined
			if(el === undefined || el === null || el.length <= 0) return false;

			var id = null;

			if(el.hasClass('cms_plugin')) {
				id = el.attr('id').replace('cms_plugin-', '');
			} else if(el.hasClass('cms_draggable')) {
				id = el.attr('id').replace('cms_draggable-', '');
			} else {
				id = el.attr('id').replace('cms_placeholder-bar-', '');
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
			$('.cms_draggable').removeClass('cms_draggable-selected');
			$('.cms_plugin').removeClass('cms_plugin-active');

			// if false is provided, only remove classes
			if(id === false) return false;

			// attach active class to current element
			var dragitem = $('#cms_draggable-' + id);
			var plugin = $('#cms_plugin-' + id);

			// collapse all previous elements
			var collapsed = dragitem.parents().siblings().not('.cms_dragitem-expanded');
				collapsed.trigger(this.click);

			// set new classes
			dragitem.addClass('cms_draggable-selected');
			plugin.addClass('cms_plugin-active');
		},

		// private methods
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
					$('.cms_droppable-empty-wrapper').show();
					// ensure all menus are closed
					$('.cms_dragitem .cms_submenu').hide();
					// remove classes from empty dropzones
					$('.cms_droppable-empty').removeClass('cms_draggable-disallowed');
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
					$('.cms_droppable-empty-wrapper').hide();

					// cancel if isAllowed returns false
					if(!that.state) return false;

					// handle dropped event
					if(dropped) {
						droparea.prepend(ui.item);
						dropped = false;
					}

					// we pass the id to the updater which checks within the backend the correct place
					var id = ui.item.attr('id').replace('cms_draggable-', '');
					var plugin = $('#cms_plugin-' + id);
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
					var original = $('#cms_plugin-' + that.getId(originalItem));
					// cancel if item has no settings
					if(original.data('settings') === undefined) return false;
					var type = original.data('settings').plugin_type;
					// prepare variables for bound
					var holder = placeholder.parent().prevAll('.cms_placeholder-bar').first();
					var plugin = $('#cms_plugin-' + that.getId(placeholder.closest('.cms_draggable')));

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
/*##################################################|*/
/* #CMS.PLACEHOLDERS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Placeholders
	 * @version: 2.0.0
	 * @description: Adds one-time placeholder handling
	 */
	CMS.Placeholders = new CMS.Class({

		initialize: function (placeholers, plugins, options) {
			this.placeholders = $(placeholers);
			this.plugins = $(plugins);
			this.options = $.extend(true, {}, this.options, options);

			this.toolbar = $('#cms_toolbar');
			this.tooltip = this.toolbar.find('.cms_placeholders-tooltip');
			this.bars = this.placeholders.find('.cms_placeholder-bar');
			this.sortables = $('.cms_draggables'); // use global scope
			this.clipboard = this.toolbar.find('.cms_clipboard');
			this.dragging = false;
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'tap.cms';

			// this.dragitems = $('.cms_draggable');
			this.dropareas = $('.cms_droppable');

			this.timer = function () {};
			this.state = false;

			// handle all draggables one time initialization
			this._setupPlaceholders(this.placeholders);
			this._setupPlugins(this.plugins);

			this._events();
			this._preventEvents();
			this._drag();
			this._clipboard();
		},

		// initial methods
		_setupPlaceholders: function (placeholders) {
			var that = this;

			// ensure collapsables work
			this._collapsables(placeholders.find('.cms_draggable'));

			// add global collapsable events
			placeholders.find('.cms_placeholder-title').bind(this.click, function () {
				($(this).hasClass('cms_placeholder-title-expanded')) ? that._collapseAll($(this)) : that._expandAll($(this));
			});

			// check which button should be shown for collapsemenu
			placeholders.each(function (index, item) {
				var els = $(item).find('.cms_dragitem-collapsable');
				var open = els.filter('.cms_dragitem-expanded');
				if(els.length === open.length && (els.length + open.length !== 0)) {
					$(item).find('.cms_placeholder-title').addClass('cms_placeholder-title-expanded');
				}
			});
		},

		_setupPlugins: function (plugins) {
			var that = this;

			plugins.bind('mouseover mouseout', function (e) {
				e.stopPropagation();
				if(e.type === 'mouseover') {
					var name = $(this).data('settings').plugin_name;
					that.tooltip.css('visibility', 'visible').show().find('span').html(name);
					that.tooltip.data('plugin_id', $(this).data('settings').plugin_id);
				} else {
					that.tooltip.css('visibility', 'hidden').hide();
				}
			});

			// attach tooltip event for touch devices
			this.tooltip.bind('touchstart.cms', function () {
				$('#cms_plugin-' + $(this).data('plugin_id')).trigger('dblclick');
			});
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

		// private methods
		_events: function () {
			var that = this;

			// this sets the correct position for the edit tooltip
			$(document.body).bind('mousemove.cms', function (e) {
				// so lets figure out where we are
				var offset = 20;
				var bound = $(document).width();
				var pos = e.pageX + that.tooltip.outerWidth(true) + offset;

				that.tooltip.css({
					'left': (pos >= bound) ? e.pageX - that.tooltip.outerWidth(true) - offset : e.pageX + offset,
					'top': e.pageY - 12
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
					that._updateClipboard(ui.item);

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

		_clipboard: function () {
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

		_updateClipboard: function () {
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
		},

		_collapsables: function (draggables) {
			var that = this;
			var settings = CMS.API.Toolbar.getSettings();

			// attach events to draggable
			draggables.find('> .cms_dragitem-collapsable').bind(this.click, function () {
				var el = $(this);
				var id = that.getId($(this).parent());
				var settings = CMS.API.Toolbar.getSettings();
					settings.states = settings.states || [];

				// collapsable function and save states
				if(el.hasClass('cms_dragitem-expanded')) {
					settings.states.splice(settings.states.indexOf(id), 1);
					el.removeClass('cms_dragitem-expanded').parent().find('> .cms_draggables').hide();
				} else {
					settings.states.push(id);
					el.addClass('cms_dragitem-expanded').parent().find('> .cms_draggables').show();
				}

				// save settings
				CMS.API.Toolbar.setSettings(settings);
			});
			// adds double click event
			draggables.bind('dblclick', function (e) {
				e.stopPropagation();
				$('#cms_plugin-' + that.getId($(this))).trigger('dblclick');
			});

			// removing dublicate entries
			var sortedArr = settings.states.sort();
			var filteredArray = [];
			for(var i = 0; i < sortedArr.length; i++) {
				if(sortedArr[i] !== sortedArr[i + 1]) {
					filteredArray.push(sortedArr[i]);
				}
			}
			settings.states = filteredArray;

			// save cleaned array
			CMS.API.Toolbar.setSettings(settings);

			// loop through the items
			$.each(CMS.API.Toolbar.getSettings().states, function (index, id) {
				var el = $('#cms_draggable-' + id);
					el.find('> .cms_draggables').show();
					el.find('> .cms_dragitem').addClass('cms_dragitem-expanded');
			});
		},

		_expandAll: function (el) {
			var items = el.closest('.cms_placeholder').find('.cms_dragitem-collapsable');
			// cancel if there are no items
			if(!items.length) return false;
			items.each(function () {
				if(!$(this).hasClass('cms_dragitem-expanded')) $(this).trigger('click.cms');
			});

			el.addClass('cms_placeholder-title-expanded');
		},

		_collapseAll: function (el) {
			var items = el.closest('.cms_placeholder').find('.cms_dragitem-collapsable');
			items.each(function () {
				if($(this).hasClass('cms_dragitem-expanded')) $(this).trigger('click.cms');
			});

			el.removeClass('cms_placeholder-title-expanded');
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

	/*!
	 * PlaceholderItem
	 * @version: 2.0.0
	 * @description: Adds individual handling
	 */
	CMS.PlaceholderItem = new CMS.Class({

		options: {
			'type': '', // bar, plugin or generic
			'placeholder_id': null,
			'plugin_type': '',
			'plugin_id': null,
			'plugin_language': '',
			'plugin_parent': null,
			'plugin_order': null,
			'plugin_breadcrumb': [],
			'plugin_restriction': [],
			'urls': {
				'add_plugin': '',
				'edit_plugin': '',
				'move_plugin': '',
				'copy_plugin': '',
				'cut_plugin': ''
			}
		},

		initialize: function (container, options) {
			this.container = $('[id="' + container + '"]');
			this.options = $.extend(true, {}, this.options, options);

			this.body = $(document);
			this.csrf = CMS.API.Toolbar.options.csrf;
			this.timer = function () {};
			this.timeout = 250;
			this.focused = false;
			this.click = (document.ontouchstart !== null) ? 'click.cms' : 'tap.cms';

			// bind data element to the container
			this.container.data('settings', this.options);

			// handler for placeholder bars
			if(this.options.type === 'bar') this._setBar();

			// handler for all generic plugins
			if(this.options.type === 'plugin') this._setPlugin();

			// handler for specific static items
			if(this.options.type === 'generic') this._setGeneric();
		},

		// initial methods
		_setBar: function () {
			// attach event to the bar menu
			this._setSubnav(this.container.find('.cms_submenu'));
		},

		_setPlugin: function () {
			var that = this;

			var plugin = this.container;
			var draggables = $('.cms_draggables');
			var draggable = $('#cms_draggable-' + this.options.plugin_id);
			var dragitem = draggable.find('> .cms_dragitem');
			var timer = function () {};

			var options = draggable.find('.cms_submenu:eq(0)');
			var allOptions = draggables.find('.cms_submenu');

			// PLUGIN EVENTS
			plugin.bind('dblclick', function (e) {
				e.preventDefault();
				e.stopPropagation();

				that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, that.options.plugin_breadcrumb);
			});

			plugin.bind('mousedown mouseup mousemove', function (e) {
				if(e.type !== 'mousemove') e.stopPropagation();

				if(e.type === 'mousedown' && (e.which !== 3 || e.button !== 2)) {
					// start countdown
					timer = setTimeout(function () {
						CMS.API.Toolbar._enableDragMode(300);
						CMS.API.Toolbar.setActive(plugin.data('settings').plugin_id);
					}, 500);
				} else {
					clearTimeout(timer);
				}
			});

			// attach event to the plugin menu
			this._setSubnav(draggable.find('> .cms_dragitem .cms_submenu'));

			// DRAGGABLE EVENTS
			dragitem.bind('mouseenter', function (e) {
				e.preventDefault();
				e.stopPropagation();

				allOptions.hide();
				options.show();
			});
			draggable.bind('mouseenter mouseleave mouseover', function (e) {
				e.preventDefault();
				e.stopPropagation();

				if(that.focused) return false;

				if(e.type === 'mouseenter' || e.type === 'mouseover') $(this).data('active', true);
				if(e.type === 'mouseleave') {
					$(this).data('active', false);
					allOptions.hide();
				}

				// add timeout to determine if we should hide the element
				setTimeout(function () {
					if(!$(e.currentTarget).data('active')) {
						$(e.currentTarget).find('.cms_submenu:eq(0)').hide();
					}
				}, 100);
			});
			draggable.find('> .cms_dragitem').bind('mousedown mouseup mousemove', function (e) {
				if(e.type === 'mousedown') {
					// start countdown
					timer = setTimeout(function () {
						CMS.API.Toolbar._enableEditMode(300);
						CMS.API.Toolbar.setActive(plugin.data('settings').plugin_id);
						$(document).bind('mousemove.keypress', function () {
							$(document).trigger('keyup.cms', [true]);
							setTimeout(function () {
								$(document).unbind('mousemove.keypress');
							}, 1000);
						});
					}, 500);
				} else {
					clearTimeout(timer);
				}
			});

			// update plugin position
			this.container.bind('cms.placeholder.update', function (e) {
				e.stopPropagation();
				that.movePlugin();
			});
		},

		_setGeneric: function () {
			var that = this;

			this.container.bind('dblclick', function (e) {
				e.preventDefault();
				that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, []);
			});

			this.container.bind('mouseenter.cms.placeholder mouseleave.cms.placeholder', function (e) {
				// add tooltip event to every placeholder
				var name = $(this).data('settings').plugin_name;
				(e.type === 'mouseenter') ? CMS.API.Placeholders.tooltip.show().find('span').html(name) : CMS.API.Placeholders.tooltip.hide();
			});
		},

		// public methods
		addPlugin: function (type, name, parent) {
			var that = this;
			var data = {
				'placeholder_id': this.options.placeholder_id,
				'plugin_type': type,
				'plugin_parent': parent || '',
				'plugin_language': this.options.plugin_language,
				'csrfmiddlewaretoken': this.csrf
			};

			$.ajax({
				'type': 'POST',
				'url': this.options.urls.add_plugin,
				'data': data,
				'success': function (data) {
					that.editPlugin(data.url, name, data.breadcrumb);
				},
				'error': function (jqXHR) {
					var msg = 'The following error occured while adding a new plugin: ';
					// trigger error
					that._showError(msg + jqXHR.status + ' ' + jqXHR.statusText);
				}
			});
		},

		editPlugin: function (url, name, breadcrumb) {
			// trigger modal window
			this._openModal(url, name, breadcrumb);
		},

		movePlugin: function () {
			var that = this;

			var plugin = $('#cms_plugin-' + this.options.plugin_id);
			var dragitem = $('#cms_draggable-' + this.options.plugin_id);

			// SETTING POSITION
			// after we insert the plugin onto its new place, we need to figure out whats above it
			var parent_id = this._getId(dragitem.prev('.cms_draggable'));

			if(parent_id) {
				// if we find a previous item, attach it afterwards
				plugin.insertAfter($('#cms_plugin-' + parent_id));
			} else {
				// if we dont find out, we need to figure out where it belongs and get the previous item
				dragitem.parent().parent().next().prepend(plugin);
			}

			// SAVING POSITION
			var placeholder_id = this._getId(dragitem.parents('.cms_draggables').last().prevAll('.cms_placeholder-bar').first());
			var plugin_parent = this._getId(dragitem.parent().closest('.cms_draggable'));
			var plugin_order = this._getIds(dragitem.siblings('.cms_draggable').andSelf());

			// cancel here if we have no placeholder id
			if(placeholder_id === false) return false;

			// gather the data for ajax request
			var data = {
				'placeholder_id': placeholder_id,
				'plugin_id': this.options.plugin_id,
				'plugin_parent': plugin_parent || '',
				 // this is a hack: when moving to different languages use the global language
				'plugin_language': this.options.page_language,
				'plugin_order': plugin_order,
				'csrfmiddlewaretoken': CMS.API.Toolbar.options.csrf
			};

			$.ajax({
				'type': 'POST',
				'url': this.options.urls.move_plugin,
				'data': data,
				'success': function (response) {
					// if response is reload
					if(response.reload) CMS.API.Helpers.reloadBrowser();

					// TODO: show only if(response.status)
					that._showSuccess(dragitem);
				},
				'error': function (jqXHR) {
					var msg = 'An error occured during the update.';
					// trigger error
					that._showError(msg + jqXHR.status + ' ' + jqXHR.statusText);
				}
			});

			// show publish button
			$('.cms_btn-publish').addClass('cms_btn-publish-active').parent().show();
		},

		copyPlugin: function (cut) {
			var that = this;
			var data = {
				'source_placeholder_id': this.options.placeholder_id,
				'source_plugin_id': this.options.plugin_id || '',
				'source_language': this.options.plugin_language,
				'target_placeholder_id': CMS.API.Toolbar.options.clipboard,
				'target_language': this.options.plugin_language,
				'csrfmiddlewaretoken': this.csrf
			};

			// determine if we are using copy or cut
			var url = (cut) ? this.options.urls.cut_plugin : this.options.urls.copy_plugin;

			$.ajax({
				'type': 'POST',
				'url': url,
				'data': data,
				'success': function () {
					// refresh browser after success
					CMS.API.Helpers.reloadBrowser();
				},
				'error': function (jqXHR) {
					var msg = 'The following error occured while copying the plugin: ';
					// trigger error
					that._showError(msg + jqXHR.status + ' ' + jqXHR.statusText);
				}
			});
		},

		// private methods
		_setSubnav: function (nav) {
			var that = this;

			nav.bind('mouseenter mouseleave tap.cms', function (e) {
				e.preventDefault();
				e.stopPropagation();
				(e.type === 'mouseenter') ? that._showSubnav($(this)) : that._hideSubnav($(this));
			});

			nav.find('a').bind('click.cms tap.cms', function (e) {
				e.preventDefault();
				e.stopPropagation();

				// show loader and make sure scroll doesn't jump
				CMS.API.Toolbar._showLoader(true);
				CMS.API.Toolbar._disableScroll(false);

				var el = $(this);

				// set switch for subnav entries
				switch(el.attr('data-rel')) {
					case 'add':
						that.addPlugin(el.attr('href').replace('#', ''), el.text(), that._getId(el.closest('.cms_draggable')));
						break;
					case 'edit':
						that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, that.options.plugin_breadcrumb);
						break;
					case 'copy':
						that.copyPlugin();
						break;
					/*case 'stack':
						//that.stackPlugin();
						break;*/
					default:
						CMS.API.Toolbar._showLoader(false);
						that._delegate(el);
				}
			});

			nav.find('input').bind('keyup focus blur click', function (e) {
				if(e.type === 'focus') that.focused = true;
				if(e.type === 'blur') {
					that.focused = false;
					that._hideSubnav(nav);
				}
				if(e.type === 'keyup') {
					clearTimeout(that.timer);
					// keybound is not required
					that.timer = setTimeout(function () {
						that._searchSubnav(nav, $(e.currentTarget).val());
					}, 100);
				}
			});

			// set data attributes
			nav.find('.cms_submenu-dropdown').each(function () {
				$(this).data('top', $(this).css('top'))
			});

			// prevent propagnation
			nav.bind(this.click, function (e) {
				e.stopPropagation();
			});
		},

		_showSubnav: function (nav) {
			var that = this;
			var dropdown = nav.find('.cms_submenu-dropdown');
			var offset = parseInt(dropdown.data('top'));

			// clearing
			clearTimeout(this.timer);

			// add small delay before showing submenu
			this.timer = setTimeout(function () {
				// reset z indexes
				var reset = $('.cms_placeholder .cms_submenu').parentsUntil('.cms_placeholder');
					reset.css('z-index', 0);

				var parents = nav.parentsUntil('.cms_placeholder');
					parents.css('z-index', 999);

				// show subnav
				nav.find('.cms_submenu-quicksearch').show();

				// set visible states
				nav.find('> .cms_submenu-dropdown').show();
			}, 100);

			// add key events
			$(document).unbind('keydown.cms');
			$(document).bind('keydown.cms', function (e) {
				var anchors = nav.find('.cms_submenu-item:visible a');
				var index = anchors.index(anchors.filter(':focus'));

				// bind arrow down and tab keys
				if(e.keyCode === 40 || e.keyCode === 9) {
					e.preventDefault();
					if(index >= 0 && index < anchors.length - 1) {
						anchors.eq(index + 1).focus();
					} else {
						anchors.eq(0).focus();
					}
				}

				// bind arrow up keys
				if(e.keyCode === 38) {
					e.preventDefault();
					if(anchors.is(':focus')) {
						anchors.eq(index - 1).focus();
					} else {
						anchors.eq(anchors.length).focus();
					}
				}

				// hide subnav when hitting enter or escape
				if(e.keyCode === 13 || e.keyCode === 27) {
					that._hideSubnav(nav);
				}
			});

			if($(window).height() + $(window).scrollTop() - nav.offset().top - dropdown.height() <= 10) {
				dropdown.css('top', 'auto');
				dropdown.css('bottom', offset + 4);
			} else {
				dropdown.css('top', offset);
				dropdown.css('bottom', 'auto');
			}

			// enable scroll
			CMS.API.Toolbar._disableScroll(true);

			// set relativity
			$('.cms_placeholder').css({
				'position': 'relative',
				'z-index': 99
			});
			nav.closest('.cms_placeholder').css('z-index', 999);
		},

		_hideSubnav: function (nav) {
			clearTimeout(this.timer);

			var that = this;
			// cancel if quicksearch is focues
			if(this.focused) return false;

			// set correct active state
			nav.closest('.cms_draggable').data('active', false);

			this.timer = setTimeout(function () {
				// set visible states
				nav.find('> .cms_submenu-dropdown').hide();
				nav.find('.cms_submenu-quicksearch').hide();
				// reset search
				nav.find('input').val('');
				that._searchSubnav(nav, '');
			}, this.timeout);

			// enable scroll
			CMS.API.Toolbar._disableScroll(false);

			// reset relativity
			$('.cms_placeholder').css('position', '');
		},

		_searchSubnav: function (nav, value) {
			var items = nav.find('.cms_submenu-item');
			var titles = nav.find('.cms_submenu-item-title');

			// cancel if value is zero
			if(value === '') {
				items.add(titles).show();
				return false;
			}

			// loop through items and figure out if we need to hide items
			items.find('a, span').each(function (index, item) {
				item = $(item);
				var text = item.text().toLowerCase();
				var search = value.toLowerCase();

				(text.indexOf(search) >= 0) ? item.parent().show() : item.parent().hide();
			});

			// check if a title is matching
			titles.filter(':visible').each(function (index, item) {
				titles.hide();
				$(item).nextUntil('.cms_submenu-item-title').show();
			});

			// always display title of a category
			items.filter(':visible').each(function (index, item) {
				if($(item).prev().hasClass('cms_submenu-item-title')) {
					$(item).prev().show();
				} else {
					$(item).prevUntil('.cms_submenu-item-title').last().prev().show();
				}
			});

			// if there is no element visible, show only first categoriy
			nav.find('.cms_submenu-dropdown').show();
			if(items.add(titles).filter(':visible').length <= 0) {
				nav.find('.cms_submenu-dropdown').hide();
			}
		},

		_getId: function (el) {
			return CMS.API.Placeholders.getId(el);
		},

		_getIds: function (els) {
			var array = [];
			els.each(function () {
				array.push(CMS.API.Placeholders.getId($(this)));
			});
			return array;
		},

		_openModal: function (url, name, breadcrumb) {
			return CMS.API.Toolbar.openModal(url, name, breadcrumb);
		},

		_showError: function (msg) {
			return CMS.API.Toolbar.showError(msg);
		},

		_showSuccess: function (el) {
			var tpl = $('<div class="cms_dragitem-success"></div>');
			el.append(tpl);
			// start animation
			tpl.fadeOut(function () {
				$(this).remove()
			});
		},

		_delegate: function (el) {
			return CMS.API.Toolbar._delegate(el);
		}

	});

});
})(CMS.$);

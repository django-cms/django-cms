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
			var draggables = placeholders.find('.cms_draggable');

			// attach events to draggable
			draggables.find('> .cms_dragitem-collapsable').bind('click', function () {
				var el = $(this);
				var id = that.getId($(this).parent());
				var settings = CMS.API.Toolbar.getSettings();
					settings.states = settings.states || [];
				var index = settings.states.indexOf(id);
				if(index != -1) settings.states.splice(settings.states.indexOf(id), 1);

				if(el.hasClass('cms_dragitem-collapsed')) {
					// show element
					el.removeClass('cms_dragitem-collapsed').parent().find('> .cms_draggables').show();
				} else {
					// hide element
					el.addClass('cms_dragitem-collapsed').parent().find('> .cms_draggables').hide();
					settings.states.push(id);
				}

				// save settings
				CMS.API.Toolbar.setSettings(settings);
			});

			// setting correct states
			var states = CMS.API.Toolbar.getSettings().states;
			// loop through the items
			$.each(states, function (index, id) {
				var el = $('#cms_draggable-' + id);
					el.find('> .cms_draggables').hide();
					el.find('> .cms_dragitem').addClass('cms_dragitem-collapsed');
			});
		},

		_setupPlugins: function (plugins) {
			var that = this;

			plugins.bind('mouseover mouseout', function (e) {
				e.stopPropagation();
				// add events to placeholder
				(e.type === 'mouseover') ? that.tooltip.show() : that.tooltip.hide();
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
				that.tooltip.css({
					'left': e.pageX + 20,
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
					$('.cms_droppable-empty-wrapper').slideDown(200);
					// ensure all menus are closed
					$('.cms_dragitem .cms_submenu').hide();
					// remove classes from empty dropzones
					$('.cms_droppable-empty').removeClass('cms_draggable-disallowed');
					// fixes placeholder height
					ui.placeholder.height(ui.item.height());
				},

				'stop': function (event, ui) {
					that.dragging = false;
					// hide empty
					$('.cms_droppable-empty-wrapper').slideUp(200);

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
				},
				'isAllowed': function(placeholder, placeholderParent, originalItem) {
					// getting restriction array
					var bounds = [];
					// save original state events
					var original = $('#cms_plugin-' + that.getId(originalItem));
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
			remove.bind('click', function (e) {
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

		_preventEvents: function () {
			var clicks = 0;
			var delay = 500;
			var timer = function () {};
			var prevent = true;

			// unbind click event if already initialized
			this.plugins.find('a, button, input[type="submit"], input[type="button"]').bind('click', function (e) {
				if(prevent) {
					e.preventDefault();

					// clear timeout after click and increment
					clearTimeout(timer);

					timer = setTimeout(function () {
						// if there is only one click use standard event
						if(clicks === 1) {
							prevent = false;

							$(e.currentTarget)[0].click();
						}
						// reset
						clicks = 0;
					}, delay);

					clicks++;
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
				'copy_plugin': ''
			}
		},

		initialize: function (container, options) {
			this.container = $(container);
			this.options = $.extend(true, {}, this.options, options);

			this.body = $(document);
			this.csrf = CMS.API.Toolbar.options.csrf;
			this.timer = function () {};
			this.timeout = 250;
			this.focused = false;
			this.keyBound = 1;

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

				if(e.type === 'mousedown') {
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

			// update plugin position
			this.container.bind('cms.placeholder.update', function (e) {
				e.stopPropagation();
				that.movePlugin();
			});
		},

		_setGeneric: function () {
			var that = this;

			this.container.bind('dblclick', function () {
				that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, []);
			});

			this.container.bind('mouseenter.cms.placeholder mouseleave.cms.placeholder', function (e) {
				// add tooltip event to every placeholder
				(e.type === 'mouseenter') ? CMS.API.Placeholders.tooltip.show() : CMS.API.Placeholders.tooltip.hide();
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
					if(response === 'success') that._showSuccess(dragitem);

					// determin if we should refresh
					// if(parseInt(that.options.placeholder_id) === parseInt(CMS.API.Toolbar.options.clipboard)) CMS.API.Helpers.reloadBrowser();
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

		copyPlugin: function () {
			var that = this;
			var data = {
				'source_placeholder_id': this.options.placeholder_id,
				'source_plugin_id': this.options.plugin_id || '',
				'source_language': this.options.plugin_language,
				'target_placeholder_id': CMS.API.Toolbar.options.clipboard,
				'target_language':  this.options.plugin_language,
				'csrfmiddlewaretoken': this.csrf
			};

			$.ajax({
				'type': 'POST',
				'url': this.options.urls.copy_plugin,
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

			nav.bind('mouseenter mouseleave', function (e) {
				e.preventDefault();
				e.stopPropagation();
				(e.type === 'mouseenter') ? that._showSubnav($(this)) : that._hideSubnav($(this));
			});

			nav.find('a').bind('click', function (e) {
				e.preventDefault();
				e.stopPropagation();

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
					case 'stack':
						// that.stackPlugin();
						break;
					default:
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
					// cancel if we have less than x keys
					if($(this).val().length < that.keyBound) return false;
					that.timer = setTimeout(function () {
						that._searchSubnav(nav, $(e.currentTarget).val());
					}, 100);
				}
			});

			// prevent propagnation
			nav.bind('click', function (e) {
				e.stopPropagation();
			});
		},

		_showSubnav: function (nav) {
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
		},

		_searchSubnav: function (nav, value) {
			// loop through items and figure out if we need to hide items
			nav.find('.cms_submenu-item a').each(function (index, item) {
				var text = $(item).text().toLowerCase();
				var search = value.toLowerCase();

				(text.indexOf(search) >= 0 || search === '') ? $(this).parent().show() : $(this).parent().hide();
			});
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
			return CMS.API.Toolbar.delegate(el);
		}

	});

});
})(CMS.$);
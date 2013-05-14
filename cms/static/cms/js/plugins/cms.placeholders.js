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
				this.menu = this.toolbar.find('.cms_placeholders-menu');
				this.bars = this.placeholders.find('.cms_placeholder-bar');
				this.sortables = $('.cms_draggables'); // use global scope
				this.clipboard = this.toolbar.find('.cms_clipboard');

				// this.dragitems = $('.cms_draggable');
				this.dropareas = $('.cms_droppable');

				this.timer = function () {};
				this.state = false;

				// handle all draggables one time initialization
				this._setupPlaceholders(this.placeholders);
				this._setupPlugins(this.plugins);

				this._events();
				this._preventEvents();
				this._dragging();
				this._clipboard();
			},

			_setupPlaceholders: function (placeholders) {
				var that = this;
				var draggables = placeholders.find('.cms_draggable');

				draggables.bind('mouseenter mouseleave', function (e) {
					e.stopPropagation();
					// add events to dragholder
					(e.type === 'mouseenter') ? that._showMenu($(this)) : that._hideMenu($(this));
				});

				// TODO we need to define the initial state and expanded behaviour
				draggables.find('> .cms_dragitem-collapsable').bind('click', function (e) {
					$(this).toggleClass('cms_dragitem-collapsed')
						.parent().find('> ul').toggle();
				});
			},

			_setupPlugins: function (plugins) {
				var that = this;

				plugins.bind('mouseover mouseout', function (e) {
					e.stopPropagation();
					// add events to placeholder
					(e.type === 'mouseover') ? that.tooltip.show() : that.tooltip.hide();
					(e.type === 'mouseover') ? that._showMenu($(this)) : that._hideMenu($(this));
				});
			},

			_events: function () {
				var that = this;

				// this sets the correct position for the edit tooltip
				$(document.body).bind('mousemove', function (e) {
					that.tooltip.css({
						'left': e.pageX + 20,
						'top': e.pageY - 12
					});
				});

				// bind menu specific events so its not hidden when hovered
				this.menu.bind('mouseover mouseout', function (e) {
					e.stopPropagation();
					(e.type === 'mouseover') ? that._showMenu($(this)) : that._hideMenu();
				});
			},

			_showMenu: function (el) {
				// clear timer
				clearTimeout(this.timer);

				// handle class handling
				if(el.hasClass('cms_draggable')) this.menu.addClass('cms_placeholders-menu-alternate');

				// hide all settings
				$('.cms_draggable .cms_submenu').hide();

				// exclude if hovering menu itself
				if(!el.hasClass('cms_placeholders-menu')) {
					this.menu.css({
						'left': el.offset().left,
						'top': el.offset().top
					});
					// show element and attach id to CMS.Toolbar
					this.menu.show().data('id', this.getId(el));
				}
			},

			_hideMenu: function () {
				var that = this;
				var timeout = 200;

				clearTimeout(this.timer);

				// sets the timer for closing
				this.timer = setTimeout(function () {
					that.menu.fadeOut(50, function () {
						that.menu.removeClass('cms_placeholders-menu-alternate');
					});
				}, timeout);
			},

			_collapse: function () {},

			_expand: function () {},

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

			_dragging: function () {
				var that = this;
				var dropped = false;
				var droparea = null;

				this.sortables.nestedSortable({
					'items': '.cms_draggable',
					'handle': '.cms_dragitem',
					'listType': 'ul',
					'opacity': 0.4,
					'tolerance': 'pointer',
					'toleranceElement': '> div',
					'cursor': 'move',
					'connectWith': this.sortables,
					// creates a cline thats over everything else
					'helper': 'clone',
					'appendTo': 'body',
					'dropOnEmpty': true,
					'forcePlaceholderSize': true,
					'placeholder': 'cms_droppable',
					'zIndex': 999999,
					'isAllowed': function(placeholder, placeholderParent, originalItem) {
						// getting restriction array
						var bounds = [];
						var plugin = $('#cms_plugin-' + that.getId(originalItem));

						var bar = placeholder.parent().prevAll('.cms_placeholder-bar').first();
						var type = plugin.data('settings').plugin_type;

						// now set the correct bounds
						if(plugin.length) bounds = plugin.data('settings').plugin_restriction;
						if(bar.length) bounds = bar.data('settings').plugin_restriction;

						// if restrictions is still empty, proceed
						that.state = ($.inArray(type, bounds) !== -1) ? true : false;

						return that.state;
					},
					'start': function () {
						// show empty
						$('.cms_droppable-empty-wrapper').slideDown(200);
					},
					'stop': function (event, ui) {
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
					},
					'disableNestingClass': 'cms_draggable-disabled',
					'errorClass': 'cms_draggable-disallowed',
					'hoveringClass': 'cms_draggable-hover'
					// TODO not yet required
					// branchClass: 'mjs-nestedSortable-branch',
					// collapsedClass: 'mjs-nestedSortable-collapsed',
					// expandedClass: 'cms_draggable-disallowed',
					// leafClass: 'mjs-nestedSortable-leaf',
				});

				// define droppable helpers
				this.dropareas.droppable({
					'greedy': true,
					'accept': '.cms_draggable',
					'tolerance': 'pointer',
					'activeClass': 'cms_draggable-allowed',
					'hoverClass': 'cms_draggable-hover-allowed',
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
				var containers = this.clipboard.find('.cms_clipboard-containers > li');
				var position = 220;
				var speed = 100;

				// add remove event
				remove.bind('click', function (e) {
					e.preventDefault();
					// TODO remove all entries
				});

				// add events to paste
				triggers.bind('click mouseenter', function (e) {
					e.preventDefault();

					containers.stop().css({ 'left': -position });
					containers.eq(triggers.index(this)).stop().animate({ 'left': 0 }, speed);
				});
				containers.bind('mouseleave', function () {
					containers.stop().css({ 'left': -position });
				});
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
				this.keyBound = 3;

				// handler for placeholder bars
				if(this.options.type === 'bar') this._setBar();

				// handler for all generic plugins
				if(this.options.type === 'plugin') this._setPlugin();

				// handler for specific static items
				if(this.options.type === 'generic') this._setGeneric();

				// bind data element to the container
				this.container.data('settings', this.options);
			},

			_setBar: function () {
				// attach event to the bar menu
				this._setSubnav(this.container.find('.cms_submenu'));
			},

			_setPlugin: function () {
				var that = this;

				// CONTENT
				this.container.bind('dblclick', function (e) {
					e.preventDefault();
					e.stopPropagation();

					that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, that.options.plugin_breadcrumb);
				});

				var draggable = $('#cms_draggable-' + this.options.plugin_id);
				// attach event to the plugin menu
				this._setSubnav(draggable.find('> .cms_dragitem .cms_submenu'));

				// only show button when hovering the plugin
				draggable.bind('mouseenter mouseleave mousemove', function (e) {
					e.stopPropagation();

					if(e.type === 'mouseenter') draggable.find('.cms_submenu').show();
					if(e.type === 'mouseleave') draggable.find('.cms_submenu').hide();
					if(e.type === 'mousemove') draggable.trigger('mouseenter');
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

				// gather the data for ajax request
				var data = {
					'placeholder_id': placeholder_id,
					'plugin_id': this.options.plugin_id,
					'plugin_parent': plugin_parent || '',
					'plugin_language': this.options.plugin_language,
					'plugin_order': plugin_order,
					'csrfmiddlewaretoken': CMS.API.Toolbar.options.csrf
				};

				$.ajax({
					'type': 'POST',
					'url': this.options.urls.move_plugin,
					'data': data,
					'success': function (response) {
						if(response === 'success') that._showSuccess(dragitem);
					},
					'error': function (jqXHR) {
						var msg = 'An error occured during the update.';
						// trigger error
						that._showError(msg + jqXHR.status + ' ' + jqXHR.statusText);
					}
				})
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
					'success': function (data) {
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

			// API helpers
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

				nav.find('input').bind('keyup focus blur', function (e) {
					if(e.type === 'focus') that.focused = true;
					if(e.type === 'blur') {
						that.focused = false;
						that._hideSubnav(nav);
					}
					if(e.type === 'keyup') {
						clearTimeout(that.timer);
						// cancel if we have less than x keys
						if($(this).val().length < this.keyBound) return false;
						that.timer = setTimeout(function () {
							that._searchSubnav(nav, $(e.currentTarget).val());
						}, 100);
					}
				});
			},

			_showSubnav: function (nav) {
				clearTimeout(this.timer);

				// we need to hide previous menu
				$('.cms_submenu > ul').hide()
					.parent().css('z-index', 0).end()
					.parents('.cms_placeholder').andSelf().css('z-index', 0);

				nav.parent().css('z-index', 9999);
				nav.parents('.cms_placeholder').andSelf().css('z-index', 999);
				nav.find('> ul').show();
				// show quicksearch only at a certain height
				if(nav.find('> ul').height() >= 230) {
					nav.find('.cms_submenu-quicksearch').show();
					// we need to set a fixed height for the search
					nav.find('> ul').css('height', 230);
				}
			},

			_hideSubnav: function (nav) {
				var that = this;
				// cancel if quicksearch is focues
				if(this.focused) return false;

				this.timer = setTimeout(function () {
					nav.parent().css('z-index', 999);
					nav.parents('.cms_placeholder').andSelf().css('z-index', 99);
					nav.find('> ul').hide();
					nav.find('.cms_submenu-quicksearch').hide();
					// reset search
					nav.find('input').val('');
					that._searchSubnav(nav, '');
				}, this.timeout);
			},

			_searchSubnav: function (nav, value) {
				// loop through items and figure out if we need to hide items
				nav.find('li a').each(function (index, item) {
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
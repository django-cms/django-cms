/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * Plugins
	 * for created plugins or generics (static content)
	 */
	CMS.Plugin = new CMS.Class({

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
			this.csrf = CMS.config.csrf;
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

			// set collapsables
			if(this.options.type === 'bar' || this.options.type === 'plugin') this._collapsables();
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
						CMS.API.StructureBoard.setActive(plugin.data('settings').plugin_id);
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
						CMS.API.StructureBoard.setActive(plugin.data('settings').plugin_id);
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

			// adds tooltip behaviour
			this.container.bind('mouseover.cms mouseout.cms', function (e) {
				e.stopPropagation();
				var name = $(this).data('settings').plugin_name;
				var id = $(this).data('settings').plugin_id;
				(e.type === 'mouseover') ? CMS.API.Helpers.showTooltip(name, id) : CMS.API.Helpers.hideTooltip();
			});
		},

		_setGeneric: function () {
			var that = this;

			this.container.bind('dblclick', function (e) {
				e.preventDefault();
				that.editPlugin(that.options.urls.edit_plugin, that.options.plugin_name, []);
			});

			this.container.bind('mouseover.cms mouseout.cms', function (e) {
				e.stopPropagation();
				var name = $(this).data('settings').plugin_name;
				var id = $(this).data('settings').plugin_id;
				(e.type === 'mouseover') ? CMS.API.Helpers.showTooltip(name, id) : CMS.API.Helpers.hideTooltip();
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
			var modal = new CMS.Modal();
				modal.open(url, name, breadcrumb);
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
				'csrfmiddlewaretoken': this.csrf
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
				CMS.API.Toolbar._loader(true);
				CMS.API.Helpers.preventScroll(false);

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
						CMS.API.Toolbar._loader(false);
						CMS.API.Toolbar._delegate(el);
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
			this.preventScroll(true);

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
			this.preventScroll(false);

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

		_collapsables: function () {
			var that = this;
			var settings = CMS.API.Toolbar.getSettings();
			var draggable = $('#cms_draggable-' + this.options.plugin_id);

			// ONLY FOR BARS
			// add global collapsable events
			this.container.find('.cms_placeholder-title').bind(this.click, function () {
				($(this).hasClass('cms_placeholder-title-expanded')) ? that._collapseAll($(this)) : that._expandAll($(this));
			});
			// check which button should be shown for collapsemenu
			this.container.each(function (index, item) {
				var els = $(item).find('.cms_dragitem-collapsable');
				var open = els.filter('.cms_dragitem-expanded');
				if(els.length === open.length && (els.length + open.length !== 0)) {
					$(item).find('.cms_placeholder-title').addClass('cms_placeholder-title-expanded');
				}
			});

			// ONLY FOR DRAGGABLE
			if(!draggable.length) return false;
			// attach events to draggable
			draggable.find('> .cms_dragitem-collapsable').bind(this.click, function () {
				var el = $(this);
				var id = that._getId($(this).parent());
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
			draggable.bind('dblclick', function (e) {
				e.stopPropagation();
				$('#cms_plugin-' + that._getId($(this))).trigger('dblclick');
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

		_getId: function (el) {
			return CMS.API.StructureBoard.getId(el);
		},

		_getIds: function (els) {
			return CMS.API.StructureBoard.getIds(els);
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
		}

	});

});
})(CMS.$);
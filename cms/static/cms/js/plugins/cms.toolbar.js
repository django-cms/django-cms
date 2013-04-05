/*##################################################|*/
/* #CMS.TOOLBAR# */
CMS.$(document).ready(function ($) {
	// assign correct jquery to $ namespace
	$ = CMS.$ || $;

	/*!
	 * Toolbar
	 * @public_methods:
	 *	- CMS.API.Toolbar.toggleToolbar();
	 *	- CMS.API.Toolbar.registerItem(obj);
	 *	- CMS.API.Toolbar.registerItems(array);
	 *	- CMS.API.Toolbar.removeItem(id);
	 *	- CMS.API.Toolbar.registerType(function);
	 *  - CMS.API.Toolbar.isToolbarHidden();
	 * @compatibility: IE >= 6, FF >= 2, Safari >= 4, Chrome > =4, Opera >= 10
	 * TODO: login needs special treatment (errors, login on enter)
	 * TODO: styling of the collapser button needs to be somehow transparent
	 */
	CMS.Toolbar = CMS.Class.$extend({

		implement: [CMS.API.Helpers, CMS.API.Security],

		options: {
			'debug': false, // not integrated yet
			'items': []
		},

		initialize: function (container, options) {
			// save reference to this class
			var that = this;
			// check if only one element is given
			if($(container).length > 2) { throw new Error('Toolbar Error: one element expected, multiple elements given.'); }
			// merge passed argument options with internal options
			this.options = $.extend(this.options, options);

			// set initial variables
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.toolbar.left = this.toolbar.find('.cms_toolbar-left');
			this.toolbar.right = this.toolbar.find('.cms_toolbar-right');

			// bind event to toggle button so toolbar can be shown/hidden
			this.toggle = this.wrapper.find('#cms_toolbar-toggle');
			this.toggle.bind('click', function (e) {
				e.preventDefault();
				that.toggleToolbar();
			});

			// initial setups
			this._setup();
		},

		/**
		 * All methods with an underscore as prefix should not be called through the API namespace
		 */
		_setup: function () {
			// save reference to this class
			var that = this;

			// scheck if toolbar should be shown or hidden
			($.cookie('CMS_toolbar-collapsed') == 'false') ? this.toolbar.data('collapsed', true) : this.toolbar.data('collapsed', false);
			// follow up script to set the current state
			this.toggleToolbar();

			// set toolbar to visible
			this.wrapper.show();
			// some browsers have problem showing it directly (loading css...)
			setTimeout(function () { that.wrapper.show(); }, 50);

			// start register items if any given
			if(this.options.items.length) this.registerItems(this.options.items);

			// apply csrf patch to toolbar from cms.base.js
			this.csrf();

			// the toolbar needs to resize depending on the window size on ie6
			if($.browser.msie && $.browser.version <= '6.0') {
				$(window).bind('resize', function () { that.wrapper.css('width', $(window).width()); });
				$(window).trigger('resize');
			}
		},
		
		// Checks whether the toolbar is hidden right now
		isToolbarHidden: function(){
			return this.toolbar.data('collapsed');
		},

		/**
		 * Binds the collapsed data element to the toolbar
		 * Calls private methods _showToolbar and _hideToolbar when required
		 * Saves current state in a cookie
		 */
		toggleToolbar: function () {
			(this.toolbar.data('collapsed')) ? this._showToolbar() : this._hideToolbar();

			return this.toolbar.data('collapsed');
		},

		// sets collapsed data to false
		_showToolbar: function () {
			// add toolbar padding
			var padding = parseInt($(document.body).css('margin-top'));
				$(document.body).css('margin-top', (padding+43)); // 43 = height of toolbar
			// show toolbar
			this.toolbar.show();
			// change data information
			this.toolbar.data('collapsed', false);
			// add class to trigger
			this.toggle.addClass('cms_toolbar-collapsed');
			// save as cookie
			$.cookie('CMS_toolbar-collapsed', false, { path:'/', expires:7 });
			// add show event to toolbar
			this.toolbar.trigger('cms.toolbar.show');
		},

		// sets collapsed data to true
		_hideToolbar: function () {
			// remove toolbar padding
			var padding = parseInt($(document.body).css('margin-top'));
				$(document.body).css('margin-top', (padding-this.toolbar.height()-1)); // substract 1 cause of the border
			// hide toolbar
			this.toolbar.hide();
			// change data information
			this.toolbar.data('collapsed', true);
			// remove class from trigger
			this.toggle.removeClass('cms_toolbar-collapsed');
			// save as cookie
			$.cookie('CMS_toolbar-collapsed', true, { path:'/', expires:7 });
			// add hide event to toolbar
			this.toolbar.trigger('cms.toolbar.hide');
		},

		/**
		 * Handles the different item types and redirects them to their private method
		 * @param: obj (object that represents the item data to be registered)
		 */
		registerItem: function (obj) {
			// error handling
			if(typeof(obj) !== 'object') return false;
			if(!obj.order) obj.dir = 0;

			// check for internal types
			switch(obj.type) {
				case 'anchor':
					this._registerAnchor(obj);
					break;
				case 'html':
					this._registerHtml(obj);
					break;
				case 'switcher':
					this._registerSwitcher(obj);
					break;
				case 'button':
					this._registerButton(obj);
					break;
				case 'list':
					this._registerList(obj);
					break;
				default:
					this.registerType(obj);
			}

			return obj;
		},

		/**
		 * This public method allows multiple addition of registerItems within one call
		 * @param: items (array of objects)
		 */
		registerItems: function (items) {
			// make sure an array is passed
			if(typeof(items) !== 'object') return false;
			// save reference to this class
			var that = this;
			// loopp through all items and pass them to single function
			$(items).each(function (index, value) {
				that.registerItem(value);
			});

			return items;
		},

		/**
		 * Removes the item with a specific id. This is not in use yet
		 * @param: index
		 */
		removeItem: function (index) {
			if(typeof(index) !== 'number') return false;
			// function to remove an item
			$($('.cms_toolbar-item')[index]).remove();

			return index;
		},

		// requires: type, order, dir, title, url
		// optional: cls
		_registerAnchor: function (obj) {
			// take a copy of the template, append it, remove it, copy html. required because of how jquery works.
			var template = this._processTemplate('#cms_toolbar-item_anchor', obj);
			// fixes href issue on ie7
			template.find('a').bind('click', function (e) {
				e.preventDefault();
				// redirect to correct url
				window.location.href = obj.url;
			});
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		// required: type, order, dir, html || htmlElement
		// optional: cls, redirect
		_registerHtml: function (obj) {
			// here we dont need processTemplate cause we create the template
			var template = (obj.html) ? $(obj.html) : $(obj.htmlElement);
			// add order, show item
			template.data('order', obj.order).css('display', 'block');
			// add class if neccessary
			if(obj.cls) template.addClass(obj.cls);
			// special case for form html
			template.find('.cms_toolbar-btn').bind('click', function (e) {
				e.preventDefault();
				(obj.redirect) ? document.location = obj.redirect : $(this).parentsUntil('form').parent().submit();
			});
			
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		// required: type, order, dir, removeParameter, addParameter
		// optional: cls, state
		_registerSwitcher: function (obj) {
			// save reference to this class
			var that = this;
			// take a copy of the template, append it, remove it, copy html. required because of how jquery works.
			var template = this._processTemplate('#cms_toolbar-item_switcher', obj);
			// should btn be shown?
			var btn = template.find('.cms_toolbar-item_switcher-link span');

			// initial setup
			if(obj.state) {
				btn.data('state', true).css('backgroundPosition', '0px -198px');
			} else {
				btn.data('state', false).css('backgroundPosition', '-40px -198px');
			}

			// add events
			template.find('.cms_toolbar-item_switcher-link').bind('click', function (e) {
				e.preventDefault();

				// animate toggle effect and trigger handler
				if(btn.data('state')) {
					btn.stop().animate({'backgroundPosition': '-40px -198px'}, function () {
						// disable link
						document.location = that.setUrl(document.location, {
							'addParam': obj.removeParameter,
							'removeParam': obj.addParameter
						});
					});
				} else {
					btn.stop().animate({'backgroundPosition': '0px -198px'}, function () {
						// enable link
						document.location = that.setUrl(document.location, {
							'addParam': obj.addParameter,
							'removeParam': obj.removeParameter
						});
					});
				}
			});
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		// required: type, order, dir, redirect
		// optional: cls, icon, action, hidden
		_registerButton: function (obj) {
			// take a copy of the template, append it, remove it, copy html. required because of how jquery works.
			var template = this._processTemplate('#cms_toolbar-item_button', obj);
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		// required: type, order, dir, items (title, url, method (get/post), cls, icon)
		// optional: cls, icon
		_registerList: function (obj) {
			// take a copy of the template, append it, remove it, copy html. required because of how jquery works.
			var template = this._processTemplate('#cms_toolbar-item_list', obj);

			// item injection logic
			var list = template.find('.cms_toolbar-item_list').html();
				// ff2 list check
				if(!list) return false;
			var tmp = '';
			// lets loop through the items
			$(obj.items).each(function (index, value) {
				// add icon if available
				var icon_styles = value.icon ? ' class="cms_toolbar_icon cms_toolbar_icon-enabled" style="background-image:url('+value.icon+');"' : '';
				// add ie 7 and below fix to urls
				if($.browser.msie && $.browser.version <= 7) value.url = value.url.replace('/', '');
				// replace attributes
				tmp += list.replace('[list_title]', value.title)
						   .replace('[list_url]', value.url)
						   .replace('[list_method]', value.method)
						   .replace('[list_class]', value.cls)
						   .replace('<span>', '<span'+icon_styles+'>');
			});
			// add items
			template.find('.cms_toolbar-item_list').html($(tmp));

			// add events
			var container = template.find('.cms_toolbar-item_list');
			var btn = template.find('.cms_toolbar-btn');
				btn.data('collapsed', true)
				   .bind('click', function (e) {
					e.preventDefault();
					($(this).data('collapsed')) ? show_list() : hide_list();
			});

			// add form action if rel equals get or post
			var anchors = container.find('a');
			if(anchors.attr('rel') === 'POST') {
				// loop through the items and attach post events
				anchors.each(function (index, item) {
					if($(item).attr('rel') === 'POST') {
						$(item).unbind('click').bind('click', function (e) {
							e.preventDefault();
							// attach form action
							$.ajax({
								'type': $(e.currentTarget).attr('rel'),
								'url': $(e.currentTarget).attr('href'),
								'data': $(e.currentTarget).attr('href').split('?')[1],
								'success': function () {
									CMS.API.Helpers.reloadBrowser();
								},
								'error': function () {
									throw new Error('CMS.Toolbar was unable to perform this ajax request. Try again or contact the developers.');
								}
							});
							// after clicking hide list
							hide_list();
						});
					}
				});
			}

			function show_list() {
				// add event to body to hide the list needs a timout for late trigger
				setTimeout(function () {
					$(document).bind('click', hide_list);
				}, 100);

				// show element and save data
				container.show();
				btn.addClass('cms_toolbar-btn-active').data('collapsed', false);
			}
			function hide_list() {
				// remove the body event
				$(document).unbind('click');

				// show element and save data
				container.hide();
				btn.removeClass('cms_toolbar-btn-active').data('collapsed', true);
			}

			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		/**
		 * Basic API to add more types rather than the predefined (anchor, html, switcher, button, list)
		 * @param: handler (function)
		 */
		registerType: function (handler) {
			// invoke function
			if(typeof(handler) === 'function') handler();

			return handler;
		},

		// parses passed templates from items
		_processTemplate: function (id, obj) {
			// lets find the template and clone it
			var template = this.wrapper.find(id).clone();
				template = $('<div>').append(template).clone().remove().html();
			// replace placeholders
			if(obj.title) template = template.replace('[title]', obj.title);
			if(obj.url) template = template.replace('[url]', obj.url);
			if(!obj.icon && obj.type === 'button') template = template.replace('&nbsp;', '').replace('&nbsp;', '');
			// template = template.replace('[token]', this.options.csrf_token);
			template = (obj.action) ? template.replace('[action]', obj.action) : template.replace('[action]', '');
			template = (obj.hidden) ? template.replace('[hidden]', obj.hidden) : template.replace('[hidden]', '');
			// back to jquery object
			template = $(template);
			if(obj.cls) template.addClass(obj.cls);
			if (obj.icon) {
				template.find('.cms_toolbar-btn_right .toolbar_icon-prefix')
						.addClass('cms_toolbar_icon-enabled')
						.css('background-image', 'url('+obj.icon+')');
			}
			// add events
			template.find('.cms_toolbar-btn').bind('click', function (e) {
				e.preventDefault();
				(obj.redirect) ? document.location = obj.redirect : $(this).parentsUntil('form').parent().submit();
			});
			// save order remove id and show element
			template.data('order', obj.order)
					.attr('id', '') /* remove initial id */
					.css('display', 'block');

			return template;
		},

		// appends item in correct order and position
		_injectItem: function (el, dir, order) {
			// save some vars
			var left = this.toolbar.left;
			var right = this.toolbar.right;

			if(dir === 'left') {
				var leftContent = left.find('> *');
					if(!leftContent.length) { left.append(el); return false; }

				// first insert it at start position
				el.insertBefore($(leftContent[0]));

				// and what happens if there is already an element?
				leftContent.each(function (index, item) {
					// sava data from element
					var current = $(item).data('order');
					// inject data when current is lower, repeat till element fits position
					if(order >= current || order == current) el.insertAfter($(item));
				});
			}

			if(dir === 'right') {
				var rightContent = right.find('> *');
					if(!rightContent.length) { right.append(el); return false; }

				// first insert it at start position
				el.insertBefore($(rightContent[0]));

				rightContent.each(function (index, item) {
					// save data from element
					var current = $(item).data('order');
					// inject data when current is lower, repeat till element fits position
					if(order >= current || order == current) el.insertAfter($(item));
				});
			}
		}

	});
});
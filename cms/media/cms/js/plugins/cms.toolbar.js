(function ($) {
/**
 * @author:		Angelo Dini
 * @copyright:	http://www.divio.ch under the BSD Licence
 * @requires:	Classy, jQuery, jQuery.cookie
 */

/*##################################################|*/
/* #CMS.TOOLBAR# */
jQuery(document).ready(function ($) {

	/**
	 * Toolbar
	 * @version: 0.1.2
	 * @description: Implements and controls toolbar
	 * @public_methods:
	 *	- CMS.Toolbar.toggleToolbar();
	 *	- CMS.Toolbar.registerItem(obj);
	 *	- CMS.Toolbar.registerItems(array);
	 *	- CMS.Toolbar.removeItem(id);
	 *	- CMS.Toolbar.registerType(function);
	 * @compatibility: IE >= 6, FF >= 2, Safari >= 4, Chrome > =4, Opera >= 10
	 * TODO: login needs special treatment (errors, login on enter)
	 */
	CMS.Toolbar = CMS.Class.$extend({

		implement: [CMS.Helpers, CMS.Security],

		options: {
			'debug': false, // not integrated yet
			'items': []
		},

		initialize: function (container, options) {
			// save reference to this class
			var that = this;
			// check if only one element is given
			if($(container).length > 2) { log('Toolbar Error: one element expected, multiple elements given.'); return false; }
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

			// the toolbar needs to resize depending on the window size on motherfucking ie6
			if($.browser.msie && $.browser.version <= '6.0') {
				$(window).bind('resize', function () { that.wrapper.css('width', $(window).width()); })
				$(window).trigger('resize');
			}
		},

		toggleToolbar: function () {
			(this.toolbar.data('collapsed')) ? this._showToolbar() : this._hideToolbar();

			return this;
		},

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

		registerItem: function (obj) {
			// error handling
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

		registerItems: function (items) {
			// make sure an array is passed
			if(typeof(items) != 'object') return false;
			// save reference to this class
			var that = this;
			// loopp through all items and pass them to single function
			$(items).each(function (index, value) {
				that.registerItem(value);
			});

			return items;
		},

		removeItem: function (index) {
			// function to remove an item
			if(index) $($('.cms_toolbar-item:visible')[index]).remove();

			return index;
		},

		_registerAnchor: function (obj) {
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_anchor', obj);
			this._injectItem(template, obj.dir, obj.order);
		},

		_registerHtml: function (obj) {
			// here we dont need processTemplate cause we create the template
			var template = (obj.html) ? $(obj.html) : $(obj.htmlElement);
			// add order, show item
			template.data('order', obj.order).css('display', 'block');
			// add class if neccessary
			if(obj.cls) template.addClass(obj.cls);
			// add events
			template.find('.cms_toolbar-btn').bind('click', function (e) {
				e.preventDefault();
				(obj.redirect) ? document.location = obj.redirect : $(this).parentsUntil('form').parent().submit();
			});
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		_registerSwitcher: function (obj) {
			// save reference to this class
			var that = this;
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
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
						var url = that.removeUrl(document.location.href, obj.addParameter);
						document.location = that.insertUrl(url, obj.removeParameter, "")
					});
				} else {
					btn.stop().animate({'backgroundPosition': '0px -198px'}, function () {
						// enable link
						document.location = that.insertUrl(location.href, obj.addParameter, "");
					});
				}
			});
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		_registerButton: function (obj) {
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_button', obj);
			// append item
			this._injectItem(template, obj.dir, obj.order);
		},

		_registerList: function (obj) {
			// take a copy of the template, append it, remove it, copy html... because jquery is stupid
			var template = this._processTemplate('#cms_toolbar-item_list', obj);

			// item injection logic
			var list = template.find('.cms_toolbar-item_list').html();
				// ff2 list check
				if(!list) return false;
			var tmp = '';
			// lets loop through the items
			$(obj.items).each(function (index, value) {
				// add icon if available
				// TODO: backend needs to return '' instead of '/media/None'
				var icon = (value.icon !== '/media/None') ? 'cms_toolbar_icon cms_toolbar_icon-enabled ' : '';
				// replace attributes
				tmp += list.replace('[list_title]', value.title)
						   .replace('[list_url]', value.url)
						   .replace('<span>', '<span class="'+icon+'" style="background-image:url('+value.icon+');">');
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

		registerType: function (handler) {
			// invoke function
			if(typeof(handler) == 'function') handler();

			return handler;
		},

		/* this private method processes each template and replaces the placeholders with the passed values */
		_processTemplate: function (cls, obj) {
			// lets find the template and clone it
			var template = this.wrapper.find(cls).clone();
				template = $('<div>').append(template).clone().remove().html();
			// replace placeholders
			if(obj.title) template = template.replace('[title]', obj.title);
			if(obj.url) template = template.replace('[url]', obj.url);
			if(!obj.icon && obj.type == 'button') template = template.replace('&nbsp;', '').replace('&nbsp;', '');
			// template = template.replace('[token]', this.options.csrf_token);
			template = (obj.action) ? template.replace('[action]', obj.action) : template.replace('[action]', '');
			template = (obj.hidden) ? template.replace('[hidden]', obj.hidden) : template.replace('[hidden]', '');
			// back to jquery object
			template = $(template);
			if(obj.cls) template.addClass(obj.cls);
			// TODO: backend should return '' or undefined instead of /media/
			if(obj.icon && obj.icon !== '/media/') {
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

		_injectItem: function (el, dir, order) {
			// save some vars
			var left = this.toolbar.left;
			var right = this.toolbar.right;

			if(dir == 'left') {
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

			if(dir == 'right') {
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

})(jQuery);
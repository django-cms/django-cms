/**
 * @author		Angelo Dini
 * @copyright	http://www.divio.ch under the BSD Licence
 * @requires	Classy, jQuery
 *
 * check if classy.js exists */
 if(window['Class'] === undefined) log('classy.js is required!');

/*##################################################|*/
/* #CUSTOM APP# */
(function ($, Class) {
	/**
	 * Toolbar
	 * @version: 0.0.1
	 */
	CMS.Toolbar = Class.$extend({

		options: {
			'page_is_defined': false,
			'edit_mode': false
		},

		initialize: function (el, options) {
			// save reference to this class
			var classy = this;
			// check if only one element is found
			if($(el).length > 2) { log('Toolbar Error: one element expected, multiple elements given.'); return false; }
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save toolbar elements
			this.wrapper = $(el);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.toolbar.left = this.toolbar.find('.cms_toolbar-left');
			this.toolbar.right = this.toolbar.find('.cms_toolbar-right');
			this.dim = this.wrapper.find('#cms_toolbar-dim');
			
			// bind event to toggle button
			this.toggle = this.wrapper.find('#cms_toolbar-toggle');
			this.toggle.bind('click', function (e) {
				e.preventDefault();
				classy.toggleToolbar();
			});
			
			// csrf security patch
			patchCsrf(jQuery);
			
			// initial setups
			this._setup();
		},
		
		_setup: function () {
			// set if toolbar is visible or not
			($.cookie('CMS_toolbar-collapsed') == 'false') ? this.toolbar.data('collapsed', true) : this.toolbar.data('collapsed', false);
			
			// init scripts
			this.toggleToolbar();
			//this.toggleDim();
		},
		
		toggleToolbar: function () {
			(this.toolbar.data('collapsed')) ? this._showToolbar() : this._hideToolbar();
		},
		
		_showToolbar: function () {
			var classy = this;
			// add toolbar padding
			var padding = parseInt($(document.body).css('padding-top'));
				setTimeout(function () {
					$(document.body).css('padding-top', (padding+classy.toolbar.height()));
				}, 50);
			// show toolbar
			this.toolbar.show();
			// change data information
			this.toolbar.data('collapsed', false);
			// add class to trigger
			this.toggle.addClass('cms_toolbar-collapsed');
			// save as cookie
			$.cookie('CMS_toolbar-collapsed', false, { path:'/', expires:7 });
		},
		
		_hideToolbar: function () {
			// remove toolbar padding
			var padding = parseInt($(document.body).css('padding-top'));
				$(document.body).css('padding-top', (padding-this.toolbar.height()));
			// hide toolbar
			this.toolbar.hide();
			// change data information
			this.toolbar.data('collapsed', true);
			// remove class from trigger
			this.toggle.removeClass('cms_toolbar-collapsed');
			// save as cookie
			$.cookie('CMS_toolbar-collapsed', true, { path:'/', expires:7 });
		},
		
		toggleDim: function () {
			(this.toolbar.data('dimmed')) ? this._showDim() : this._hideDim();
		},
		
		_showDim: function () {
			var classy = this;
			// stop window from scrolling
			$(document.body).css('overflow', 'hidden');
			// init dim resize
			this.dim.css({
				'width': $(window).width(),
				'height': $(window).height(),
			});
			// attach resize event to window
			$(window).bind('resize', function () {
				classy.dim.css({
					'width': $(window).width(),
					'height': $(window).height(),
				});
			});
			// change data information
			this.toolbar.data('dimmed', false);
			// show dim
			this.dim.stop().fadeIn();
		},
		
		_hideDim: function () {
			// retain window from scrolling
			$(document.body).css('overflow', 'auto');
			// unbind resize event
			$(window).unbind('resize');
			// change data information
			this.toolbar.data('dimmed', true);
			// hide dim
			this.dim.css('opcaity', 0.6).stop().fadeOut();
		},
		
		registerItem: function (item, order) {
			// save vars with fallbacks
			var el = $(item.el);
				if(!el.length) return false;
			var dir = (item.dir) ? item.dir : 'right';
			var order = (order) ? parseInt(order) : 0;
			
			// check for internal types
			switch(item.type) {
				case 'anchor':
					this._registerAnchor(el, dir, order);
					break;
				case 'switcher':
					this._registerSwitcher(el, dir, order, item);
					break;
				case 'button':
					this._registerButton(el, dir, order, item);
					break;
				default:
					this.registerType(item, order);
			}
		},
		
		registerItems: function (items) {
			// make sure an array is passed
			if(typeof(items) != 'object') return false;
			// save reference to this class
			var classy = this;
			// loopp through all items and pass them to single function
			$(items).each(function (index, item) {
				if(item.order) index = item.order;
				classy.registerItem(item, index);
			});
		},
		
		registerType: function () {
			log('you want new type?');
		},
		
		_registerAnchor: function (el, dir, order) {
			// save and show element data
			el.data('order', order)
			  .css('display', 'block');
			
			// append item
			this._injectItem(el, dir, order);
		},
		
		_registerSwitcher: function (el, dir, order, opt) {
			// save reference to this class
			var classy = this;
			// save and show element data
			el.data('order', order)
			  .css('display', 'block')
			
			// should btn be shown?
			var btn = el.find('.cms_toolbar-item_switcher-link span');
			
			// initial setup
			if(opt.state == 'on') {
				btn.data('state', 'on').css('backgroundPosition', '0px -198px');
			} else {
				btn.data('state', 'off').css('backgroundPosition', '-40px -198px');
			}
			
			el.find('.cms_toolbar-item_switcher-link').bind('click', function (e) {
				e.preventDefault();
				
				// animate toggle effect and trigger handler
				if(btn.data('state') == 'on') {
					btn.stop().animate({'backgroundPosition': '-40px -198px'}, function () {
						// disable link
						var url = classy._removeUrl(window.location.href, opt.addParameter);
						window.location = classy._insertUrl(url, opt.removeParameter, "")
					});
				} else {
					btn.stop().animate({'backgroundPosition': '0px -198px'}, function () {
						// enable link
						window.location = classy._insertUrl(location.href, opt.addParameter, "");
					});
				}
				
			});
			
			// append item
			this._injectItem(el, dir, order);
		},
		
		_registerButton: function (el, dir, order, opt) {
			// save and show element data
			el.data('order', order)
			  .css('display', 'block');
			
			// append item
			this._injectItem(el, dir, order);
		},
		
		_injectItem: function (el, dir, order) {
			// save some vars
			var left = this.toolbar.left;
			var right = this.toolbar.right;
			
			if(dir == 'left') {
				var leftContent = left.find('> *');
					if(!leftContent.length) { left.append(el); return false; }
				
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
				
				rightContent.each(function (index, item) {
					// save data from element
					var current = $(item).data('order');
					// inject data when current is lower, repeat till element fits position
					if(order >= current || order == current) el.insertAfter($(item));
				});
			}
		},
		
		_insertUrl: function (url, name, value) {
			if(url.substr(url.length-1, url.length)== "&") url = url.substr(0, url.length-1); 
			dash_splits = url.split("#");
			url = dash_splits[0];
			var splits = url.split(name + "=");
			if(splits.length == 1) splits = url.split(name);
			var get_args = false;
			if(url.split("?").length>1) get_args = true;
			if(splits.length > 1){
				var after = "";
				if(splits[1].split("&").length > 1) after = splits[1].split("&")[1];
				url = splits[0] + name;
				if(value) url += "=" + value
				url += "&" + after;
			} else {
				if(get_args) { url = url + "&" + name; } else { url = url + "?" + name; }
				if(value) url += "=" + value;
			}
			if(dash_splits.length>1) url += '#' + dash_splits[1];
			if(url.substr(url.length-1, url.length)== "&") url = url.substr(0, url.length-1);
			
			return url;
		},
		
		_removeUrl: function (url, name) {
			var dash_splits = url.split("#");
			url = dash_splits[0];
			var splits = url.split(name + "=");
			if(splits.length == 1) splits = url.split(name);
			if(splits.length > 1){
				var after = "";
				if (splits[1].split("&").length > 1) after = splits[1].split("&")[1];
				if (splits[0].substr(splits[0].length-2, splits[0].length-1)=="?" || !after) {
					url = splits[0] + after;
				} else {
					url = splits[0] + "&" + after;
				}
			}
			if(url.substr(url.length-1,1) == "?") url = url.substr(0, url.length-1);
			if(dash_splits.length > 1 && dash_splits[1]) url += "#" + dash_splits[1];
			
			return url;
		}

	});
	
	//CMS.Collapse
	// need some awesome show hide effects
	
	// new Toolbar();
})(jQuery, Class);
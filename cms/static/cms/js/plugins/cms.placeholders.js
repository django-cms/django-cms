(function ($) {
/**
 * @requires:	Classy, jQuery, jQuery.ui.core, jQuery.ui.draggable, jQuery.ui.droppable
 */

/*##################################################|*/
/* #CMS.PLACEHOLDERS# */
jQuery(document).ready(function ($) {
	/**
	 * Placeholders
	 * @version: 1.0.0
	 * @description: Handles placeholders when in editmode and adds "lightbox" to toolbar
	 * @public_methods:
	 *	- CMS.API.Placeholder.addPlugin(obj, url);
	 *	- CMS.API.Placeholder.editPlugin(placeholder_id, plugin_id);
	 *	- CMS.API.Placeholder.deletePlugin(placeholder_id, plugin_id, plugin);
	 *	- CMS.API.Placeholder.toggleFrame();
	 *	- CMS.API.Placeholder.toggleDim();
	 * @compatibility: IE >= 6, FF >= 2, Safari >= 4, Chrome > =4, Opera >= 10
	 */

	CMS.Placeholders = CMS.Class.$extend({

		options: {
			'debug': false, // not integrated yet
			'edit_mode': false,
			'lang': {
				'move_warning': '',
				'delete_request': '',
				'cancel': 'Cancel'
			}
		},

		initialize: function (container, options) {
			// save reference to this class
			var that = this;
			// merge argument options with internal options
			this.options = $.extend(this.options, options);
			
			// save placeholder elements
			this.wrapper = $(container);
			this.toolbar = this.wrapper.find('#cms_toolbar-toolbar');
			this.dim = this.wrapper.find('#cms_placeholder-dim');
			this.frame = this.wrapper.find('#cms_placeholder-content');
			this.timer = null;
			this.overlay = this.wrapper.find('#cms_placeholder-overlay');
			this.overlayIsHidden = false;
			this.success = this.wrapper.find('#cms_placeholder-success');

			// setup everything
			this._setup();
		},
		
		_setup: function () {
			// save reference to this class
			var that = this;
			
			// set default dimm value to false
			this.dim.data('dimmed', false);
			
			// set defailt frame value to true
			this.frame.data('collapsed', true);
			
			// bind overlay event
			this.overlay.bind('mouseleave', function () {
				that.hideOverlay();
			});
			// this is for testing
			this.overlay.find('.cms_placeholder-overlay_bg').bind('click', function () {
				that.hideOverlay();
				
				// we need to hide the oberlay and stop the event for a while
				that.overlay.css('visibility', 'hidden');
				
				// add timer to show element after second mouseenter
				setTimeout(function () {
					that.overlayIsHidden = true;
				}, 100);
			});
		},

		addPlugin: function (values, addUrl, editUrl) {
			var that = this;
			// do ajax thingy
			$.ajax({
				'type': 'POST',
				'url': addUrl,
				'data': values,
				'success': function (response) {
					// we get the id back
					that.editPlugin.call(that, values.placeholder_id, response, editUrl);
				},
				'error': function () {
					throw new Error('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});
		},
		
		editPlugin: function (placeholder_id, plugin_id, url) {
			var that = this;
			var frame = this.frame.find('.cms_placeholder-content_inner');
			var needs_collapsing = false;
			
			// If the toolbar is hidden, editPlugin does not work properly,
			// therefore we show toggle it and save the old state.
			if (CMS.API.Toolbar.isToolbarHidden()){
				CMS.API.Toolbar.toggleToolbar();
				needs_collapsing = true;
			}
			
			// show framebox
			this.toggleFrame();
			this.toggleDim();
			
			// load the template through the data id
			// for that we create an iframe with the specific url
			var iframe = $('<iframe />', {
				'id': 'cms_placeholder-iframe',
				'src': url + placeholder_id + '/edit-plugin/' + plugin_id + '?popup=true&no_preview',
				'style': 'width:100%; height:0; border:none; overflow:auto;',
				'allowtransparency': true,
				'scrollbars': 'no',
				'frameborder': 0
			});
			
			// inject to element
			frame.html(iframe);
			
			// bind load event to injected iframe
			$('#cms_placeholder-iframe').load(function () {
				// set new height and animate
				// set a timeout for slower javascript engines (such as IE)
				setTimeout(function () {
					var height = $('#cms_placeholder-iframe').contents().find('body').outerHeight(true)+26;
					$('#cms_placeholder-iframe').animate({ 'height': height }, 500);
				}, 100);

				// remove loader class
				frame.removeClass('cms_placeholder-content_loader');

				// add cancel button
				var btn = $(this).contents().find('input[name^="_save"]');
					btn.addClass('default').css('float', 'none');
					btn.bind('click', function(){
						// If the toolbar was hidden before we started editing
						// this plugin, and it is NOT hidden now, hide it
						if (needs_collapsing && ! CMS.API.Toolbar.isToolbarHidden()){
							CMS.API.Toolbar.toggleToolbar();
						}
					})
				var cancel = $(this).contents().find('input[name^="_cancel"]');
					cancel.bind('click', function (e) {
						e.preventDefault();
						// hide frame
						that.toggleFrame();
						that.toggleDim();
						// If the toolbar was hidden before we started editing
						// this plugin, and it is NOT hidden now, hide it
						if (needs_collapsing && ! CMS.API.Toolbar.isToolbarHidden()){
							CMS.API.Toolbar.toggleToolbar();
						}
					});

				// do some css changes in template
				$(this).contents().find('#footer').css('padding', 0);
			});
			
			// we need to set the body min height to the frame height
			$(document.body).css('min-height', this.frame.outerHeight(true));
		},
		
		deletePlugin: function (plugin, plugin_id, url) {
			// lets ask if you are sure
			var message = this.options.lang.delete_request;
			var confirmed = confirm(message, true);

			// now do ajax
			if(confirmed) {
				$.ajax({
					'type': 'POST',
					'url': url,
					'data': { 'plugin_id': plugin_id },
					'success': function () {
						// remove plugin from the dom
						plugin.remove();
					},
					'error': function () {
						throw new Error('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			}
		},

		movePluginPosition: function (dir, plugin, values, url) {
			// save reference to this class
			var that = this;
			// get all siblings within the placeholder
			var holders = plugin.siblings('.cms_placeholder').andSelf();
			// get selected index and bound
			var index = holders.index(plugin);
			var bound = holders.length;

			// if the there is only 1 element, we dont need to move anything
			if(bound <= 1) {
				alert(this.options.lang.move_warning);
				return false;
			}

			// create the array
			var array = [];

			holders.each(function (index, item) {
				array.push($(item).data('options').plugin_id);
			});
			// remove current array
			array.splice(index, 1);

			// we need to check the boundary and modify the index if item jups to top or bottom
			if(index <= 0 && dir === 'moveup') {
				index = bound+1;
			} else if(index >= bound-1 && dir === 'movedown') {
				index = -1;
			}
			// add array to new position
			if(dir === 'moveup') array.splice(index-1, 0, values.plugin_id);
			if(dir === 'movedown') array.splice(index+1, 0, values.plugin_id);

			// now lets do the ajax request
			$.ajax({
				'type': 'POST',
				'url': url,
				'data': { 'ids': array.join('_') },
				'success': refreshPluginPosition,
				'error': function () {
					throw new Error('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});

			// lets refresh the elements in the dom as well
			function refreshPluginPosition() {
				if(dir === 'moveup' && index !== bound+1) plugin.insertBefore($(holders[index-1]));
				if(dir === 'movedown' && index !== -1) plugin.insertAfter($(holders[index+1]));
				// move in or out of boundary
				if(dir === 'moveup' && index === bound+1) plugin.insertAfter($(holders[index-2]));
				if(dir === 'movedown' && index === -1) plugin.insertBefore($(holders[index+1]));

				// close overlay
				that.hideOverlay();

				// show success overlay for a second
				that.success.css({
					'width': plugin.width()-2,
					'height': plugin.height()-2,
					'left': plugin.offset().left,
					'top': plugin.offset().top
				}).show().fadeOut(1000);
			}
		},

		morePluginOptions: function (plugin, values, url) {
			// save reference to this class
			var that = this;

			// how do we figure out all the placeholder names
			var array = [];
			$('.cms_placeholder-bar').each(function (index, item) {
				// TODO: get the data from the bar
				array.push($(item).attr('class').split('::')[1]);
			});

			// so whats the current placeholder?
			var current = plugin.attr('class').split('::')[1];

			// lets remove current from array - puke
			// unfortunately, Internet Explorer does not support indexOf, so
			// we use the jQuery cross browers compatible version
			var idx = $.inArray(current, array);
				array.splice(idx, 1);

			// grab the element
			var more = that.overlay.find('.cms_placeholder-options_more');
				more.show();

			var list = more.find('ul');

			// we need to stop if the array is empty
			if(array.length) list.html('');

			// loop through the array
			$(array).each(function (index, slot) {
				// do some brainfuck
				var text = $('.cms_placeholder-bar[class$="cms_placeholder_slot::' + slot + '"]').find('.cms_placeholder-title').text();
				list.append($('<li><a href="">' +text + '</a></li>').data({
					'slot': slot,
					'placeholder_id': values.placeholder,
					'plugin_id': values.plugin_id
				}));
			});

			// now we need to bind events to the elements
			list.find('a').bind('click', function (e) {
				e.preventDefault();
				// save slot var
				var slot = $(this).parent().data('slot');
				var placeholder_id = $(this).parent().data('placeholder_id');
				// now lets do the ajax request
				$.ajax({
					'type': 'POST',
					'url': url,
					'data': { 'placeholder': slot, 'placeholder_id': placeholder_id, 'plugin_id': $(this).parent().data('plugin_id') },
					'success': function () {
						refreshPluginPosition(slot);
					},
					'error': function () {
						throw new Error('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			});

			// if request is successfull move the plugin
			function refreshPluginPosition(slot) {
				// lets replace the element
				var els = $('.cms_placeholder[class$="cms_placeholder::' + slot + '"]');
				var length = els.length;

				if(els.length === 0) {
					plugin.insertAfter($('.cms_placeholder-bar[class$="cms_placeholder_slot::' + slot + '"]'));
				} else {
					plugin.insertAfter($(els.toArray()[els.length-1]));
				}

				// close overlay
				that.hideOverlay();

				// show success overlay for a second
				that.success.css({
					'width': plugin.width()-2,
					'height': plugin.height()-2,
					'left': plugin.offset().left,
					'top': plugin.offset().top
				}).show().fadeOut(1000);

				// we have to assign the new class slot to the moved plugin
				var cls = plugin.attr('class').split('::');
					cls.pop();
					cls.push(slot);
					cls = cls.join('::');
				plugin.attr('class', cls);
			}
		},

		showOverlay: function (holder) {
			// lets place the overlay
			this.overlay.css({
				'width': holder.width()-2,
				'height': holder.height()-2,
				'left': holder.offset().left,
				'top': holder.offset().top
			}).show();
		},
		
		hideOverlay: function () {
			// hide overlay again
			this.overlay.hide();
			// also hide submenu
			this.overlay.find('.cms_placeholder-options_more').hide();
		},
		
		showPluginList: function (el) {
			// save reference to this class
			// TODO: make sure the element is really shown over everything
			var that = this;
			var list = el.parent().find('.cms_placeholder-subnav');
				list.show();

			// add event to body to hide the list needs a timout for late trigger
			setTimeout(function () {
				$(document).bind('click', function () {
					that.hidePluginList.call(that, el);
				});
			}, 100);
			
			// Since IE7 (and lower) do not properly support z-index, do a cross browser hack
			if($.browser.msie && $.browser.version < '8.0') el.parent().parent().css({'position': 'relative','z-index': 999999});

			el.addClass('cms_toolbar-btn-active').data('collapsed', false);
		},
		
		hidePluginList: function (el) {
			var list = el.parent().find('.cms_placeholder-subnav');
				list.hide();

			// remove the body event
			$(document).unbind('click');

			// Since IE7 (and lower) do not properly support z-index, do a cross browser hack
			if($.browser.msie && $.browser.version < '8.0') el.parent().parent().css({'position': '','z-index': ''});

			el.removeClass('cms_toolbar-btn-active').data('collapsed', true);
		},

		toggleFrame: function () {
			(this.frame.data('collapsed')) ? this._showFrame() : this._hideFrame();
		},
		
		_showFrame: function () {
			var that = this;
			// show frame
			this.frame.fadeIn();
			// change data information
			this.frame.data('collapsed', false);
			// set dynamic frame position
			var offset = 43;
			var pos = $(document).scrollTop();
			// frame should always have space on top
			this.frame.css('top', pos+offset);
			// make sure that toolbar is visible
			if(this.toolbar.data('collapsed')) CMS.Toolbar.API._showToolbar();
			// listen to toolbar events
			this.toolbar.bind('cms.toolbar.show cms.toolbar.hide', function (e) {
				(e.handleObj.namespace === 'show.toolbar') ? that.frame.css('top', pos+offset) : that.frame.css('top', pos);
			});
		},
		
		_hideFrame: function () {
			// hide frame
			this.frame.fadeOut();
			// change data information
			this.frame.data('collapsed', true);
			// there needs to be a function to unbind the loaded content and reset to loader
			this.frame.find('.cms_placeholder-content_inner')
				.addClass('cms_placeholder-content_loader')
				.html('');
			// remove toolbar events
			this.toolbar.unbind('cms.toolbar.show cms.toolbar.hide');
		},

		toggleDim: function () {
			(this.dim.data('dimmed')) ? this._hideDim() : this._showDim();
		},
		
		_showDim: function () {
			var that = this;
			// clear timer when initiated within resize event
			if(this.timer) clearTimeout(this.timer);
			// attach resize event to window
			$(window).bind('resize', function () {
				// first we need to response to the window
				that.dim.css('height', $(window).height());
				// after a while we response to the document dimensions
				that.timer = setTimeout(function () {
					that.dim.css('height', $(document).height());
				}, 500);
			});
			// init dim resize
			// insure that onload it takes the document width
			this.dim.css('height', $(document).height());
			// change data information
			this.dim.data('dimmed', true);
			// show dim
			this.dim.css('opacity', 0.6).stop().fadeIn();
			// add event to dim to hide
			this.dim.bind('click', function () {
				that.toggleFrame.call(that);
				that.toggleDim.call(that);
			});
		},
		
		_hideDim: function () {
			// unbind resize event
			$(document).unbind('resize');
			// change data information
			this.dim.data('dimmed', false);
			// hide dim
			this.dim.css('opcaity', 0.6).stop().fadeOut();
			// remove dim event
			this.dim.unbind('click');
		}

	});

	/**
	 * Placeholder
	 * @version: 1.0.0
	 * @description: Handles each placeholder separately
	 */
	CMS.Placeholder = CMS.Class.$extend({

		initialize: function (container, options) {
			// save reference to this class
			var that = this;

			// do not merge options here
			this.options = options;
			this.container = $(container);

			// save data on item
			this.container.data('options', this.options);

			// attach event handling to placeholder buttons and overlay if editmode is active
			if(this.options.type === 'bar') {
				this._bars();
			}

			// attach events to the placeholder bars
			if(this.options.type === 'holder') {
				this.container.bind('mouseenter', function (e) {
					that._holders.call(that, e.currentTarget);
				});
			}
		},

		/* this private method controls the buttons on the bar (add plugins) */
		_bars: function () {
			// save reference to this class
			var that = this;
			var bar = this.container;

			// attach button event
			var barButton = bar.find('.cms_toolbar-btn');
				barButton.data('collapsed', true).bind('click', function (e) {
					e.preventDefault();

					($(this).data('collapsed')) ? CMS.API.Placeholders.showPluginList($(e.currentTarget)) : CMS.API.Placeholders.hidePluginList($(e.currentTarget));
				});

			// read and save placeholder bar variables
			var values = {
				'language': that.options.page_language,
				'placeholder_id': that.options.page_id,
				'placeholder': that.options.placeholder_id
			};

			// attach events to placeholder plugins
			bar.find('.cms_placeholder-subnav li a').bind('click', function (e) {
				e.preventDefault();
				// add type to values
				values.plugin_type = $(this).attr('rel').split('::')[1];

				// try to add a new plugin
				CMS.API.Placeholders.addPlugin(values, that.options.urls.add_plugin, that.options.urls.change_list);
			});
		},

		/* this private method shows the overlay when hovering */
		_holders: function (el) {
			// save reference to this class
			var that = this;
			var holder = $(el);

			// show overlay
			CMS.API.Placeholders.showOverlay(holder);

			// set overlay to visible
			if(CMS.API.Placeholders.overlayIsHidden === true) {
				CMS.API.Placeholders.overlay.css('visibility', 'visible');
				CMS.API.Placeholders.overlayIsHidden = false;
			}

			// get values from options
			var values = {
				'plugin_id': this.options.plugin_id,
				'placeholder': this.options.placeholder_id,
				'type': this.options.plugin_type,
				'slot': this.options.placeholder_slot
			};

			// attach events to each holder button
			var buttons = CMS.API.Placeholders.overlay.find('.cms_placeholder-options li');
				// unbind all button events
				buttons.find('a').unbind('click');

				// attach edit event
				buttons.find('a[rel^=edit]').bind('click', function (e) {
					e.preventDefault();
					CMS.API.Placeholders.editPlugin(values.placeholder, values.plugin_id, that.options.urls.change_list);
				});

				// attach move event
				buttons.find('a[rel^=moveup], a[rel^=movedown]').bind('click', function (e) {
					e.preventDefault();
					CMS.API.Placeholders.movePluginPosition($(e.currentTarget).attr('rel'), holder, values, that.options.urls.move_plugin);
				});

				// attach delete event
				buttons.find('a[rel^=delete]').bind('click', function (e) {
					e.preventDefault();
					CMS.API.Placeholders.deletePlugin(holder, values.plugin_id, that.options.urls.remove_plugin);
				});

				// attach more event
				buttons.find('a[rel^=more]').bind('click', function (e) {
					e.preventDefault();
					CMS.API.Placeholders.morePluginOptions(holder, values, that.options.urls.move_plugin);
				});
		}

	});

});

})(jQuery);

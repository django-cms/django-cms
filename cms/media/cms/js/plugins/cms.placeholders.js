(function ($) {
/**
 * @author:		Angelo Dini
 * @copyright:	http://www.divio.ch under the BSD Licence
 * @requires:	Classy, jQuery, jQuery.ui.core, jQuery.ui.draggable, jQuery.ui.droppable
 */

/*##################################################|*/
/* #CMS.PLACEHOLDERS# */
jQuery(document).ready(function ($) {
	/**
	 * Placeholders
	 * @version: 0.1.2
	 * @description: Handles placeholders when in editmode and adds "lightbox" to toolbar
	 * @public_methods:
	 *	- CMS.Placeholder.addPlugin(url, obj);
	 *	- CMS.Placeholder.editPlugin(placeholder_id, plugin_id);
	 *	- CMS.Placeholder.deletePlugin(placeholder_id, plugin_id, plugin);
	 *	- CMS.Placeholder.toggleFrame();
	 *	- CMS.Placeholder.toggleDim();
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
			},
			'urls': {
				'cms_page_move_plugin': '',
				'cms_page_changelist': '',
				'cms_page_change_template': '',
				'cms_page_add_plugin': '',
				'cms_page_remove_plugin': ''
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

			// attach event handling to placeholder buttons and overlay if editmode is active
			if(this.options.edit_mode) {
				this.bars = $('.cms_placeholder-bar');
				this.bars.each(function (index, item) {
					that._bars.call(that, item);
				});
				
				// enable dom traversal for cms_placeholder
				this.holders = $('.cms_placeholder');
				this.holders.bind('mouseenter', function (e) {
					that._holders.call(that, e.currentTarget);
				});
			}
			
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
				that._hideOverlay();
			});
			// this is for testing
			this.overlay.find('.cms_placeholder-overlay_bg').bind('click', function () {
				that._hideOverlay();
				
				// we need to hide the oberlay and stop the event for a while
				that.overlay.css('visibility', 'hidden');
				
				// add timer to show element after second mouseenter
				setTimeout(function () {
					that.overlayIsHidden = true;
				}, 100);
			});
		},
		
		/* this private method controls the buttons on the bar (add plugins) */
		_bars: function (el) {
			// save reference to this class
			var that = this;
			var bar = $(el);
			
			// attach button event
			var barButton = bar.find('.cms_toolbar-btn');
				barButton.data('collapsed', true).bind('click', function (e) {
					e.preventDefault();
					
					($(this).data('collapsed')) ? that._showPluginList.call(that, $(e.currentTarget)) : that._hidePluginList.call(that, $(e.currentTarget));
				});
			
			// read and save placeholder bar variables
			var split = bar.attr('class').split('::');
				split.shift(); // remove classes
			var values = {
					'language': split[0],
					'placeholder_id': split[1],
					'placeholder': split[2]
				};
			
			// attach events to placeholder plugins
			bar.find('.cms_placeholder-subnav li a').bind('click', function (e) {
				e.preventDefault();
				// add type to values
				values.plugin_type = $(this).attr('rel').split('::')[1];
				// try to add a new plugin
				that.addPlugin.call(that, that.options.urls.cms_page_add_plugin, values);
			});
		},
		
		/* this private method shows the overlay when hovering */
		_holders: function (el) {
			// save reference to this class
			var that = this;
			var holder = $(el);
			
			// show overlay
			this._showOverlay.call(that, holder);
			
			// set overlay to visible
			if(this.overlayIsHidden === true) {
				this.overlay.css('visibility', 'visible');
				this.overlayIsHidden = false;
			}
			
			// get values
			var split = holder.attr('class').split('::');
				split.shift(); // remove classes
			var values = {
					'plugin_id': split[0],
					'placeholder': split[1],
					'type': split[2],
					'slot': split[4]
				};

			// attach events to each holder button
			var buttons = this.overlay.find('.cms_placeholder-options li');
				// unbind all button events
				buttons.find('a').unbind('click');
				
				// attach edit event
				buttons.find('a[rel^=edit]').bind('click', function (e) {
					e.preventDefault();
					that.editPlugin.call(that, values.placeholder, values.plugin_id);
				});

				// attach move event
				buttons.find('a[rel^=moveup], a[rel^=movedown]').bind('click', function (e) {
					e.preventDefault();
					that._movePluginPosition.call(that, $(e.currentTarget).attr('rel'), holder, values);
				});

				// attach delete event
				buttons.find('a[rel^=delete]').bind('click', function (e) {
					e.preventDefault();
					that.deletePlugin.call(that, values.placeholder, values.plugin_id, holder);
				});

				// attach delete event
				buttons.find('a[rel^=more]').bind('click', function (e) {
					e.preventDefault();
					that._morePluginOptions.call(that, holder, values);
				});
		},
		
		addPlugin: function (url, data) {
			var that = this;
			// do ajax thingy
			$.ajax({
				'type': 'POST',
				'url': url,
				'data': data,
				'success': function (response) {
					// we get the id back
					that.editPlugin.call(that, data.placeholder_id, response);
				},
				'error': function () {
					log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
				}
			});
		},
		
		editPlugin: function (placeholder_id, plugin_id) {
			var that = this;
			var frame = this.frame.find('.cms_placeholder-content_inner');
			
			// show framebox
			this.toggleFrame();
			this.toggleDim();
			
			// load the template through the data id
			// for that we create an iframe with the specific url
			var iframe = $('<iframe />', {
				'id': 'cms_placeholder-iframe',
				'src': that.options.urls.cms_page_changelist + placeholder_id + '/edit-plugin/' + plugin_id + '?popup=true&no_preview',
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
				// cause IE is so awesome, we need a timeout so that slow rendering bitch catches up
				setTimeout(function () {
					var height = $('#cms_placeholder-iframe').contents().find('body').outerHeight(true)+26;
					$('#cms_placeholder-iframe').animate({ 'height': height }, 500);
				}, 100);

				// remove loader class
				frame.removeClass('cms_placeholder-content_loader');

				// add cancel button
				var btn = $(this).contents().find('input[name^="_save"]');
					btn.addClass('default').css('float', 'none');
				var cancel = $(this).contents().find('input[name^="_cancel"]');
					cancel.bind('click', function (e) {
						e.preventDefault();
						// hide frame
						that.toggleFrame();
						that.toggleDim();
					});

				// do some css changes in template
				$(this).contents().find('#footer').css('padding', 0);
			});
			
			// we need to set the body min height to the frame height
			$(document.body).css('min-height', this.frame.outerHeight(true));
		},
		
		deletePlugin: function (placeholder_id, plugin_id, plugin) {
			// lets ask if you are sure
			var message = this.options.lang.delete_request;
			var confirmed = confirm(message, true);

			// now do ajax
			if(confirmed) {
				$.ajax({
					'type': 'POST',
					'url': this.options.urls.cms_page_remove_plugin,
					'data': { 'plugin_id': plugin_id },
					'success': function () {
						// remove plugin from the dom
						plugin.remove();
					},
					'error': function () {
						log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
					}
				});
			}
		},
		
		_movePluginPosition: function (dir, plugin, values) {
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
				array.push($(item).attr('class').split('::')[1]);
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
				'url': this.options.urls.cms_page_move_plugin,
				'data': { 'ids': array.join('_') },
				'success': refreshPluginPosition,
				'error': function () {
					log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
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
				that._hideOverlay();

				// show success overlay for a second
				that.success.css({
					'width': plugin.width()-2,
					'height': plugin.height()-2,
					'left': plugin.offset().left,
					'top': plugin.offset().top
				}).show().fadeOut(1000);
			}
		},

		_morePluginOptions: function (plugin, values) {
			// save reference to this class
			var that = this;
			// how do we figure out all the placeholder names
			var array = [];
			$('.cms_placeholder-bar').each(function (index, item) {
				array.push($(item).attr('class').split('::')[5]);
			});

			// so whats the current placeholder=
			var current = plugin.attr('class').split('::')[5];

			// lets remove current from array - puke
			// cause ie is a fucking motherfucker it doesn't support indexOf so use jquerys crap instead
			var idx = $.inArray(current, array);
				array.splice(idx, 1);

			// grab the element
			var more = that.overlay.find('.cms_placeholder-options_more');
				more.show();

			var list = more.find('ul');

			// we need to stop if the array is empty
			if(array.length) list.html('');

			// loop through the array
			$(array).each(function (index, item) {
				// do some brainfuck
				var text = $('.cms_placeholder-bar[class$="cms_placeholder_slot::' + item + '"]').find('.cms_placeholder-title').text();
				list.append($('<li><a href="">' +text + '</a></li>').data({
					'slot': item,
					'plugin_id': values.plugin_id
				}));
			});

			// now we need to bind events to the elements
			list.find('a').bind('click', function (e) {
				e.preventDefault();
				// save slot var
				var slot = $(this).parent().data('slot');
				// now lets do the ajax request
				$.ajax({
					'type': 'POST',
					'url': that.options.urls.cms_page_move_plugin,
					'data': { 'placeholder': slot, 'plugin_id': $(this).parent().data('plugin_id') },
					'success': function () {
						refreshPluginPosition(slot);
					},
					'error': function () {
						log('CMS.Placeholders was unable to perform this ajax request. Try again or contact the developers.');
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
		
		_showOverlay: function (holder) {
			// lets place the overlay
			this.overlay.css({
				'width': holder.width()-2,
				'height': holder.height()-2,
				'left': holder.offset().left,
				'top': holder.offset().top
			}).show();
		},
		
		_hideOverlay: function () {
			// hide overlay again
			this.overlay.hide();
			// also hide submenu
			this.overlay.find('.cms_placeholder-options_more').hide();
		},
		
		_showPluginList: function (el) {
			// save reference to this class
			var that = this;
			var list = el.parent().find('.cms_placeholder-subnav');
				list.show();

			// add event to body to hide the list needs a timout for late trigger
			setTimeout(function () {
				$(document).bind('click', function () {
					that._hidePluginList.call(that, el);
				});
			}, 100);

			// ie <7 likes to be fucked on top thats cause he doesnt know z-index
			if($.browser.msie && $.browser.version < '8.0') el.parent().parent().css({'position': 'relative','z-index': 999999});

			el.addClass('cms_toolbar-btn-active').data('collapsed', false);
		},
		
		_hidePluginList: function (el) {
			var list = el.parent().find('.cms_placeholder-subnav');
				list.hide();

			// remove the body event
			$(document).unbind('click');

			// ie <7 likes to be fucked on top thats cause he doesnt know z-index
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
			if(this.toolbar.data('collapsed')) CMS.Toolbar._showToolbar();
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

			/* cause IE's mother had sex with a sheep, we need to always usw window instead of document
			 * we need to substract 4 pixel from the frame cause IE's vater has a small dick
			 * TODO: Check if scrollbars are shown, than we dont need to substract 20px, they are forced now
			 */
			var scrollbarWidth = ($.browser.msie && $.browser.version >= '8.0') ? 20 : 0;

			// attach resize event to window
			$(document).bind('resize', function () {
				that.dim.css({
					'width': $(document).width(),
					'height': $(document).height()
				});
				that.frame.css('width', $(document).width());
				// adjust after resizing
				that.timer = setTimeout(function () {
					that.dim.css({
						'width': $(document).width()-scrollbarWidth,
						'height': $(document).height()
					});
					that.frame.css('width', $(document).width()-scrollbarWidth);
				}, 500);
			});
			// init dim resize
			$(document).resize();
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
});

})(jQuery);
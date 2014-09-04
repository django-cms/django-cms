/*##################################################|*/
/* #CMS# */
(function($) {
// CMS.$ will be passed for $
$(document).ready(function () {
	/*!
	 * TreeManager
	 * Handles treeview
	 * TODO this will be refactored in 3.1
	 */
	CMS.TreeManager = new CMS.Class({

		options: {
			'lang': {}
		},

		initialize: function (options) {
			this.options = $.extend(true, {}, this.options, options);

			// load internal functions
			if(!this.options.settings.filtered) {
				this.setupFunctions();
				this.setupTreePublishing();
				this.setupUIHacks();
				this.setupGlobals();
				this.setupTree();

				// init tree component
				initTree();
			} else {
				// when filtered is active, prevent tree actions
				this.setupUIHacks();
			}
		},

		setupFunctions: function () {
			var that = this;

			$.syncCols = function(){
				$('#sitemap .col-softroot').syncWidth(0);
				$('#sitemap .col-apphook').syncWidth(0);
				$('#sitemap .col-language').syncWidth(0);
				$('#sitemap .col-navigation').syncWidth(0);
				$('#sitemap .col-actions').syncWidth(0);
				$('#sitemap .col-info').syncWidth(0);

				that.refreshColumns.call($('ul.tree-default li'));
			};

			/* Colums width sync */
			$.fn.syncWidth = function(max) {
				var visible = false;

				$(this).each(function() {
					if($(this).is(':visible')) {
						visible = true;
						var val= $(this).width();
						if(val > max){
							max = val;
						}
					}
				});
				if (visible && max > 0) {
					$(this).each(function() {
						$(this).css('width', max);
					});
				}
			};

			// jquery.functional
			$.curry = function(fn) {
				if (arguments.length < 2) return fn;
				args = $.makeArray(arguments).slice(1, arguments.length);
				return function() {
					return fn.apply(this, args.concat($.makeArray(arguments)));
				}
			};

			$.__callbackPool = {};

			$.callbackRegister = function(name, fn /*, arg0, arg1, ..*/){
				if (arguments.length > 2) {
					// create curried function
					fn = $.curry.apply(this, $.makeArray(arguments).slice(1, arguments.length));
				}
				$.__callbackPool[name] = fn;
				return name;
			};

			$.callbackCall = function(name/*, extra arg0, extra arg1, ..*/){
				if (!name || !name in $.__callbackPool) {
					throw "No callback registered with name: " + name;
				}
				$.__callbackPool[name].apply(this, $.makeArray(arguments).slice(1, arguments.length));
				$.callbackRemove(name);
				return name;
			};

			$.callbackRemove = function(name) {
				delete $.__callbackPool[name];
			};

			// very simple yellow fade plugin..
			$.fn.yft = function(){
				this.effect("highlight", {}, 1000);
			};

			// jquery replace plugin :)
			$.fn.replace = function(o) {
				return this.after(o).remove().end();
			};

		},

		setupTreePublishing: function () {
			// ADD DIRECT PUBLISHING
			var that = this;
			var tree = $('.tree');
			var langTrigger = '.col-language .trigger-tooltip span';
			var langTooltips = '.language-tooltip';
			var langTimer = function () {};
			var langDelay = 100;
			var langFadeDuration = 200;

			// show the tooltip
			tree.delegate(langTrigger, 'mouseenter', function () {
				var el = $(this).closest('.col-language').find('.language-tooltip');
				var anchors = el.find('a');
				var span = $(this);

				// clear timer
				clearTimeout(langTimer);

				// cancel if tooltip already visible
				if(el.is(':visible')) return false;

				// set correct position
				el.css('right', 20 + $(this).position().left);

				// figure out what should be shown
				anchors.hide();
				if(span.hasClass('unpublished') || span.hasClass('unpublishedparent')) anchors.eq(1).show();
				if(span.hasClass('published')) anchors.eq(0).show();
				if(span.hasClass('dirty')) anchors.show().parent().addClass('language-tooltip-multiple');

				// hide all elements
				$(langTooltips).fadeOut(langDelay);

				// use a timeout to display the tooltip
				langTimer = setTimeout(function () {
					el.stop(true, true).fadeIn(langFadeDuration);
				}, langDelay);
			});
			// hide the tooltip when leaving the area
			tree.delegate(langTrigger, 'mouseleave', function () {
				// clear timer
				clearTimeout(langTimer);
				// hide all elements
				langTimer = setTimeout(function () {
					$(langTooltips).fadeOut(langFadeDuration);
				}, langDelay * 2);
			});
			// reset hiding when entering the tooltip itself
			tree.delegate(langTooltips, 'mouseover', function () {
				// clear timer
				clearTimeout(langTimer);
			});
			tree.delegate(langTooltips, 'mouseleave', function () {
				// hide all elements
				langTimer = setTimeout(function () {
					$(langTooltips).fadeOut(langFadeDuration);
				}, langDelay * 2);
			});
			// attach double check event if publish or unpublish should be triggered
			tree.delegate('.language-tooltip a', 'click', function (e) {
				e.preventDefault();

				// cancel if not confirmed
				if(!confirm(that.options.lang.publish.replace('%s', $(this).text().toLowerCase()))) return false;

				// publish page and update
				window.location.href = $(this).attr('href');
			});
		},

		setupUIHacks: function () {
			// enables tab click on title entry to open in new window
			$('.tree').delegate('.col1 .title', 'click', function (e) {
				if(!e.metaKey) {
					window.top.location.href = $(this).attr('href');
				} else {
					window.open($(this).attr('href'), '_blank');
				}
			});

			// adds functionality to the filter
			$('#changelist-filter-button').bind('click', function () {
				$("#changelist-filter").toggle();
			});

			// set correct active entry
			if(window.parent && window.parent.CMS && window.parent.CMS.config) {
				var page_id = window.parent.CMS.config.request.page_id;

				$('div[data-page_id="'+page_id+'"]').addClass('cont-active');
			}
		},

		setupGlobals: function () {
			var that = this;
			var msg = '';
			var parent = null;

			window.moveSuccess = function(node){
				$.syncCols();

				msg = $('<span class="success">'+that.options.lang.success+'</span>');
				parent = window.parent;

				node.after(msg);
				node.parent().find('.col2').hide();
				msg.fadeOut(1000, function () {
					node.parent().find('.col2').show()
				});
				// check for reload changes
				if(window.self !== window.top) {
					window.parent.CMS.API.Helpers.reloadBrowser(false, false, true);
					window.parent.CMS.API.Toolbar.openMessage(that.options.lang.changes, false, 0);
				}
			};

			window.moveError = function(node,message){
				if(message && message !== 'error') {
					msg = $('<span class="success">'+message+'</span>');
				}
				else {
					msg = $('<span class="success">'+that.options.lang.error+'</span>');
				}
				node.parent().find('.col2').hide();
				node.after(msg);
			};

		},

		setupTree: function () {
			var that = this;
			var tree;
			// global initTree function
			initTree = function(){
				tree = new tree_component();
				var options = {
					rules: {
						clickable: "all",
						renameable: "none",
						deletable: "all",
						creatable: "all",
						draggable: "all",
						dragrules: "all",
						droppable: "all",
						metadata : "mdata",
						use_inline: true
						//droppable : ["tree_drop"]
					},
					path: false,
					ui: {
						dots: true,
						rtl: false,
						animation: 0,
						hover_mode: true,
						//theme_path: script_url_path() + "/../jstree/themes/",
						a_class: "title"
					},
					cookies : {
						prefix: "djangocms_nodes"
					},
					callback: {
						beforemove  : function(what, where, position) {
							item_id = what.id.split("page_")[1];
							target_id = where.id.split("page_")[1];
							old_node = what;

							if($(what).parent().children("li").length > 1){
								if($(what).next("li").length){
									old_target = $(what).next("li")[0];
									old_position = "right";
								}
								if($(what).prev("li").length){
									old_target = $(what).prev("li")[0];
									old_position = "left";
								}
							}else{
								if($(what).attr("rel") != "topnode"){
									old_target = $(what).parent().parent()[0];
									old_position = "inside";
								}
							}

							addUndo(what, where, position);
							return true;
						},
						onmove: function(what, where, position){
							item_id = what.id.split("page_")[1];
							target_id = where.id.split("page_")[1];

							if (position == "before") {
								position = "left";
							}else if (position == "after") {
								position = "right";
							}else if(position == "inside"){
								position = "last-child";
							}
							moveTreeItem(what, item_id, target_id, position, false);
						},

						onload: function () {
							setTimeout(function () {
								reCalc();
							}, 250);
						}

					}
				};

				if (!$($("div.tree").get(0)).hasClass('root_allow_children')){
					// disalow possibility for adding subnodes to main tree, user doesn't
					// have permissions for this
					options.rules.dragrules = ["node inside topnode", "topnode inside topnode", "node * node"];
				}

				tree.init($("div.tree"), options);
			};

			selected_page = false;
			action = false;

			var _oldAjax = $.ajax;

			$.ajax = function(s){
				// just override ajax function, so the loader message gets displayed
				// always
				$('#loader-message').show();

				callback = s.success || false;
				s.success = function(data, status){
					if (callback) {
						callback(data, status);
					}
					$('#loader-message').hide();
				};

				// just for debuging!!
				/*s.complete = function(xhr, status) {
					if (status == "error" && that.options.settings.debug) {
						$('body').before(xhr.responseText);
					}
				}*/
				// end just for debuging

				// TODO: add error state!
				return _oldAjax(s);
			};

			function refresh(){
				window.location = window.location.href;
			}

			function refreshIfChildren(pageId){
				return $('#page_' + pageId).find('li[id^=page_]').length ? refresh : function(){ return true; };
			}

			/**
			 * Loads remote dialog to dialogs div.
			 *
			 * @param {String} url
			 * @param {Object} data Data to be send over post
			 * @param {Function} noDialogCallback Gets called when response is empty.
			 * @param {Function} callback Standard callback function.
			 */
			function loadDialog(url, data, noDialogCallback, callback){
				if (data === undefined) data = {};
				$.post(url, data, function(response) {
					if (response == '' && noDialogCallback) noDialogCallback();
					$('#dialogs').empty().append(response);
					if (callback) callback(response);
				});
			}

			// let's start event delegation
			$('#changelist li').click(function(e) {
				// I want a link to check the class
				if(e.target.tagName == 'IMG' || e.target.tagName == 'SPAN') {
					target = e.target.parentNode;
				} else {
					target = e.target;
				}
				var jtarget = $(target);
				if(jtarget.hasClass("move")) {
					// prepare tree for move / cut paste
					var id = e.target.id.split("move-link-")[1];
					if(id==null){
						id = e.target.parentNode.id.split("move-link-")[1];
					}
					var page_id = id;
					selected_page = page_id;
					action = "move";
					$('span.move-target-container, span.line, a.move-target').show();
					$('#page_'+page_id).addClass("selected");
					$('#page_'+page_id+' span.move-target-container').hide();
					e.stopPropagation();
					return false;
				}

				if(jtarget.hasClass("copy")) {
					// prepare tree for copy
					id = e.target.id.split("copy-link-")[1];
					if(id==null){
						id = e.target.parentNode.id.split("copy-link-")[1];
					}
					selected_page = id;
					action = mark_copy_node(id);
					e.stopPropagation();
					return false;
				}

				if(jtarget.hasClass("viewpage")) {
					var view_page_url = $('#' + target.id + '-select').val();
					if(view_page_url){
						window.open(view_page_url);
					}
				}

				if(jtarget.hasClass("addlink")) {
					if (!/#$/g.test(jtarget.attr('href'))) {
						// if there is url instead of # inside href, follow this url
						// used if user haves add_page
						return true;
					}

					$("tr").removeClass("target");
					$("#changelist table").removeClass("table-selected");
					page_id = target.id.split("add-link-")[1];
					selected_page = page_id;
					action = "add";
					$('tr').removeClass("selected");
					$('#page-row-'+page_id).addClass("selected");
					$('.move-target-container').hide();
					$('a.move-target, span.line, #move-target-'+page_id).show();
					e.stopPropagation();
					return false;
				}

				// don't assume admin site is root-level
				// grab base url to construct full absolute URLs
				admin_base_url = document.URL.split("/cms/page/")[0] + "/";

				// in navigation
				if(jtarget.hasClass('navigation-checkbox')) {
					e.stopPropagation();

					var pageId = jtarget.attr('name').split('navigation-')[1];

					// if I don't put data in the post, django doesn't get it
					reloadItem(jtarget, admin_base_url + 'cms/page/' + pageId + '/change-navigation/', { 1:1 });
				}

				 // lazy load descendants on tree open
				if(jtarget.hasClass("closed")) {
					// only load them once
					if(jtarget.find('ul > li').length == 0 && !jtarget.hasClass("loading")) {
						// keeps this event from firing multiple times before
						// the dom as changed. it still needs to propagate for
						// the other click event on this element to fire
						jtarget.addClass("loading");
						var pageId = $(jtarget).attr("id").split("page_")[1];
						var language = $(jtarget).children('div.cont').children('div.col1').children('.title').attr('lang')
						$.get(admin_base_url + "cms/page/" + pageId + "/" + language + "/descendants/", {}, function(r, status) {
							jtarget.children('ul').append(r);
							// show move targets if needed
							if($('span.move-target-container:visible').length > 0) {
								jtarget.children('ul').find('a.move-target, span.move-target-container, span.line').show();
							}
							reCalc();
						});
					} else{
						reCalc();
					}
				}

				if(jtarget.hasClass("move-target")) {
					if(jtarget.hasClass("left")){
						position = "left";
					}
					if(jtarget.hasClass("right")){
						position = "right";
					}
					if(jtarget.hasClass("last-child")){
						position = "last-child";
					}
					target_id = target.parentNode.id.split("move-target-")[1];

					if(action=="move") {
						moveTreeItem(null, selected_page, target_id, position, tree);
						$('.move-target-container').hide();
					}else if(action=="copy") {
						site = $('#site-select')[0].value;
						copyTreeItem(selected_page, target_id, position, site);
						$('.move-target-container').hide();
					}else if(action=="add") {
						site = $('#site-select')[0].value;
						window.location.href = window.location.href.split("?")[0].split("#")[0] + 'add/?target='+target_id+"&amp;position="+position+"&amp;site="+site;
					}
					e.stopPropagation();
					return false;
				}
				return true;
			});
			$("div#sitemap").show();

			function reCalc(){
				$.syncCols();
			}

			$(window).bind('resize', reCalc);
			/* Site Selector */
			$('#site-select').change(function(){
				var form = $(this).closest('form');
				// add correct value for copy
				if(action === 'copy') $('#site-copy').val(selected_page);
				// submit form
				form.submit();
			});

			//
			// If an A element has a data-attribute 'alt-class'. At this time,
			// this is only the edit button in the page-tree, but could be
			// more in future. It is important that the CSS be written in such
			// a manner that the alt-class is defined after the normal class,
			// so that it can be overridden when the alt-key is depressed.
			//
			// NOTE: This 'preview' part of the 'alt-click to [alternative
			// function]' feature may not work in some environments (Windows
			// in a some virtual machine environments, notably), but is only a
			// nice-'extra', not a requirement for the feature.
			//
			$(document).on('keydown keyup', function(evt){
				if (evt.which === 18) {
					$('a[data-alt-class]').each(function(){
						var self = $(this);
						self.toggleClass(self.data('alt-class'), evt.type === 'keydown');
					})
				}
			});

			//
			// If the A-element has a data-attribute 'alt-href', then this
			// click-handler uses that instead of the normal href attribute as
			// the click-destination. Again, currently this is only on the
			// edit button, but could be more in future.
			//
			$('a[data-alt-href]').on('click', function(evt){
				var href;
				evt.preventDefault();
				if (evt.shiftKey) {
					href = $(this).data('alt-href');
				}
				else {
					href = $(this).attr('href');
				}
				window.location = href;					
			});

			var copy_splits = window.location.href.split("copy=");
			if(copy_splits.length > 1){
				var id = copy_splits[1].split("&")[0];
				var action = mark_copy_node(id);
				selected_page = id;
			}

			function copyTreeItem(item_id, target_id, position, site){
				if (that.options.settings.permission) {
					return loadDialog('./' + item_id + '/dialog/copy/', {
						position:position,
						target:target_id,
						site:site,
						callback: $.callbackRegister("_copyTreeItem", _copyTreeItem, item_id, target_id, position, site)
					});
				}
				return _copyTreeItem(item_id, target_id, position, site);
			}

			function _copyTreeItem(item_id, target_id, position, site, options) {
				var data = {
					position:position,
					target:target_id,
					site:site
				};
				data = $.extend(data, options);

				$.post("./" + item_id + "/copy-page/", data, function(decoded) {
					response = decoded.content;
					status = decoded.status;
					if(status==200) {
						// reload tree
						window.location = window.location.href;
					}else{
						alert(response);
						moveError($('#page_'+item_id + " div.col1:eq(0)"),response);
					}
				});
			}

			function mark_copy_node(id){
				$('a.move-target, span.move-target-container, span.line').show();
				$('#page_'+id).addClass("selected");
				$('#page_'+id).parent().parent().children('div.cont').find('a.move-target.first-child, span.second').hide();
				$('#page_'+id).parent().parent().children('ul').children('li').children('div.cont').find('a.move-target.left, a.move-target.right, span.first, span.second').hide();
				return "copy";
			}

			/**
			 * Reloads tree item (one line). If some filtering is found, adds
			 * filtered variable into posted data.
			 *
			 * @param {HTMLElement} el Any child element of tree item
			 * @param {String} url Requested url
			 * @param {Object} data Optional posted data
			 * @param {Function} callback Optional calback function
			 */
			function reloadItem(el, url, data, callback, errorCallback) {
				if (data === undefined) data = {};

				if (/\/\?/ig.test(window.location.href)) {
					// probably some filter here, tell backend, we need a filtered
					// version of item
					data['fitlered'] = 1;
				}

				function onSuccess(response, textStatus) {
					var status = true;
					var target = null;

					if(callback) status = callback(response, textStatus);
					if(status) {
						if (/page_\d+/.test($(el).attr('id'))) {
							// one level higher
							target = $(el).find('div.cont:first');
						} else {
							target = $(el).parents('div.cont:first');
						}

						var parent = target.parent();

						// remove the element if something went wrong
						if(response == 'NotFound') return parent.remove();

						var origin = $('.messagelist');
						target.replace(response);

						var messages = $(parent).find('.messagelist');
						if(messages.length) {
							origin.remove();
							messages.insertAfter('.breadcrumbs');
						}
						parent.find('div.cont:first').yft();

						// ensure after removal everything is aligned again
						$(window).trigger('resize');
					}
				}

				$.ajax({
					'type': 'POST',
					'data': data,
					'url': url,
					'success': onSuccess,
					'error': function (XMLHttpRequest, textStatus, errorThrown) {
						// errorCallback is passed through the reloadItem function
						if(errorCallback) errorCallback(XMLHttpRequest, textStatus, errorThrown);
					},
					'xhr': (window.ActiveXObject) ? function(){try {return new window.ActiveXObject("Microsoft.XMLHTTP");} catch(e) {}} : function() {return new window.XMLHttpRequest();}
				});
			}

			function moveTreeItem(jtarget, item_id, target_id, position, tree){
				reloadItem(
					jtarget, "./" + item_id + "/move-page/",

					{ position: position, target: target_id },

					// on success
					function(decoded,textStatus){
						response = decoded.content;
						status = decoded.status;
						if(status==200) {
							if (tree) {
								var tree_pos = {'left': 'before', 'right': 'after'}[position] || 'inside';
								tree.moved("#page_" + item_id, $("#page_" + target_id + " a.title")[0], tree_pos, false, false);
							} else {
								moveSuccess($('#page_'+item_id + " div.col1:eq(0)"));
							}
							return false;
						}
						else {
							moveError($('#page_'+item_id + " div.col1:eq(0)"),response);
							return false;
						}
					}
				);
			}

			var undos = [];

			function addUndo(node, target, position){
				undos.push({node:node, target:target, position:position});
			}
		},

		refreshColumns: function () {
			$('div.col2').children('div').each(function(index, item){
				$(item).css('display', 'block');
			});
			var min_width = 100000;
			var max_col2_width = 0;
			var max_col2 = null;
			$(this).each(function() {
				var cont = $(this).children('div.cont');
				if (!cont.is(':visible')) {
					return;
				}
				var col1 = cont.children('div.col1');
				var col2 = cont.children('div.col2');
				var col1_width = col1.outerWidth(true);
				var col2_width = col2.outerWidth(true);
				var total_width = cont.outerWidth(true);

				var dif = total_width - col1_width;
				if(dif < min_width){
				   min_width = dif;
				}
				if(col2_width > max_col2_width){
					max_col2_width = col2_width;
					max_col2 = col2
				}
			});

			var offset = 50;
			var w = 0;
			var hidden_count = 0;
			var max_reached = false;
			if(max_col2){
				max_col2.children('div').each(function(){
					if(!max_reached){
						w += $(this).outerWidth(true);
					}

					if(max_reached || w > (min_width - offset)){
						hidden_count = hidden_count + 1;
						max_reached = true
					}
				});

				if(hidden_count){
					$(this).each(function() {
						$(this).children('div.cont').children('div.col2').children('div').slice(-hidden_count).each(function(){
							$(this).css('display', 'none');
						})
					});
					$('div#sitemap ul.header div.col2').children().slice(-hidden_count).each(function(){
						$(this).css('display','none');
					})
				}
			}
		}

	});

});
})(CMS.$);

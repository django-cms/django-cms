/*
 * jsTree 0.9.5
 *
 * Copyright (c) 2008 Ivan Bozhanov (vakata.com)
 *
 * Dual licensed under the MIT and GPL licenses:
 *   http://www.opensource.org/licenses/mit-license.php
 *   http://www.gnu.org/licenses/gpl.html
 *
 * Date: 2009-01-03
 *
 */

// jQuery plugin
jQuery.fn.tree = function (opts) {
	return this.each(function() {
		if(tree_component.inst && tree_component.inst[jQuery(this).attr('id')]) 
			tree_component.inst[jQuery(this).attr('id')].destroy();
		if(opts !== false) {
			var tmp = new tree_component();
			tmp.init(this, opts);
		}
	});
};

// core
function tree_component () {
	// instance manager
	if(typeof tree_component.inst == "undefined") {
		tree_component.cntr = 0;
		tree_component.inst = new Array();
		tree_component.drop = new Array();

		tree_component.focusInst = function () {
			return tree_component.inst[tree_component.focused];
		}
		tree_component.mousedown = function(event) {
			var _this = tree_component.focusInst();
			if(!_this) return;
			
			var tmp = jQuery(event.target);
			if(tree_component.drop.length && tmp.is("." + tree_component.drop.join(", .")) ) {
				_this.drag = jQuery("<li id='dragged' class='dragged foreign " + event.target.className + "'><a href='#'>" + tmp.text() + "</a></li>");
				_this._drag = _this.drag;
				_this.isdown	= true;
				_this.foreign	= tmp;
				tmp.blur();
				event.preventDefault(); 
				event.stopPropagation();
				return false;
			}
			event.stopPropagation();
			return true;
		};
		tree_component.mouseup = function(event) {
			var _this = tree_component.focusInst();
			if(!_this) return;

			// CLEAR TIMEOUT FOR OPENING HOVERED NODES WHILE DRAGGING
			if(tree_component.to)	clearTimeout(tree_component.to);
			if(tree_component.sto)	clearTimeout(tree_component.sto);
			if(_this.foreign === false && _this.drag && _this.drag.parentNode && _this.drag.parentNode == jQuery(_this.container).children("ul:eq(0)").get(0)) {
				jQuery(_this.drag).remove();
				// CALL FUNCTION FOR COMPLETING MOVE
				if(_this.moveType) {
					var tmp = tree_component.inst[jQuery(_this.moveRef).parents(".tree:eq(0)").attr("id")];
					if(tmp) { 
						tmp.moved(_this.container.find("li.dragged"), _this.moveRef, _this.moveType, false, (_this.settings.rules.drag_copy == "on" || (_this.settings.rules.drag_copy == "ctrl" && event.ctrlKey) ) );
					}
				}
				_this.moveType = false;
				_this.moveRef = false;
			}
			if(_this.drag && _this.foreign !== false) {
				jQuery(_this.drag).remove();
				if(_this.moveType) {
					var tmp = tree_component.inst[jQuery(_this.moveRef).parents(".tree:eq(0)").attr("id")];
					if(tmp) { 
						tmp.settings.callback.ondrop.call(null, _this.foreign.get(0), _this.get_node( _this.moveRef).get(0), _this.moveType, _this);
					}
				}
				_this.foreign = false;
				_this.moveType = false;
				_this.moveRef = false;
			}
			// RESET EVERYTHING
			jQuery("#marker").hide();
			_this._drag		= false;
			_this.drag		= false;
			_this.isdown	= false;
			_this.appended	= false;
			_this.container.find("li.dragged").removeClass("dragged");
			event.preventDefault(); 
			event.stopPropagation();
			return false;
		};
		tree_component.mousemove = function(event) {
			var _this = tree_component.focusInst();
			if(!_this) return;

			if(_this.locked) return _this.error("LOCKED");
			if(_this.isdown) {
				// CLEAR TIMEOUT FOR OPENING HOVERED NODES WHILE DRAGGING
				if(tree_component.to) clearTimeout(tree_component.to);
				if(!_this.appended) {
					_this.container.children("ul:eq(0)").append(_this.drag);
					var tmp = jQuery(_this.drag).offsetParent();
					if(tmp.is("html")) tmp = jQuery("body");
					_this.po = tmp.offset();
					_this.appended = true;
				}
				jQuery(_this.drag).css({ "left" : (event.pageX - _this.po.left - (_this.settings.ui.rtl ? jQuery(_this.drag).width() : -5 ) ), "top" : (event.pageY - _this.po.top  + (jQuery.browser.opera ? _this.container.scrollTop() : 0) + 15) });

				if(event.target.tagName == "IMG" && event.target.id == "marker") return false;

				var cnt = jQuery(event.target).parents(".tree:eq(0)");

				// if not moving over a tree
				if(cnt.size() == 0) {
					if(tree_component.sto) clearTimeout(tree_component.sto);
					if(jQuery(_this.drag).children("IMG").size() == 0) {
						jQuery(_this.drag).append("<img class='removeicon' style='position:absolute; " + (_this.settings.ui.rtl ? "right" : "left" ) + ":4px; top:0px;' src='" + _this.settings.ui.theme_path + "default/remove.gif' />");
					}
					_this.moveType = false;
					_this.moveRef  = false;
					jQuery("#marker").hide();
					return false;
				}

				tree_component.inst[cnt.attr("id")].off_height();

				// if moving over another tree and multitree is false
				if( _this.foreign === false && cnt.get(0) != _this.container.get(0) && (!_this.settings.rules.multitree || !tree_component.inst[cnt.attr("id")].settings.rules.multitree) ) {
					if(jQuery(_this.drag).children("IMG").size() == 0) {
						jQuery(_this.drag).append("<img class='removeicon' style='position:absolute; " + (_this.settings.ui.rtl ? "right" : "left" ) + ":4px; top:0px;' src='" + _this.settings.ui.theme_path + "default/remove.gif' />");
					}
					_this.moveType = false;
					_this.moveRef  = false;
					jQuery("#marker").hide();
					return false;
				}

				if(tree_component.sto) clearTimeout(tree_component.sto);
				tree_component.sto = setTimeout( function() { tree_component.inst[cnt.attr("id")].scrollCheck(event.pageX,event.pageY); }, 50);

				var mov = false;
				var st = cnt.scrollTop();
				
				if(event.target.tagName == "A" && event.target.className=="title") {
					// just in case if hover is over the draggable
					if(jQuery(event.target).is("#dragged")) return false;

					var goTo = { 
						x : (jQuery(event.target).offset().left - 1),
						y : (event.pageY - tree_component.inst[cnt.attr("id")].offset.top)
					}
					if(cnt.hasClass("rtl")) {
						goTo.x += jQuery(event.target).width() - 8;
					}
					if( (goTo.y + st)%_this.li_height < _this.li_height/3 + 1 ) {
						mov = "before";
						goTo.y = event.pageY - (goTo.y + st)%_this.li_height - 2 ;
					}
					else if((goTo.y + st)%_this.li_height > _this.li_height*2/3 - 1 ) {
						mov = "after";
						goTo.y = event.pageY - (goTo.y + st)%_this.li_height + _this.li_height - 2 ;
					}
					else {
						mov = "inside";
						goTo.x -= 2;
						if(cnt.hasClass("rtl")) {
							goTo.x += 36;
						}
						goTo.y = event.pageY - (goTo.y + st)%_this.li_height + Math.floor(_this.li_height/2) - 2 ;
						if(_this.get_node(event.target).hasClass("closed")) {
							tree_component.to = setTimeout( function () { _this.open_branch(_this.get_node(event.target)); }, 500);
						}
					}

					if(tree_component.inst[cnt.attr("id")].checkMove(_this.container.find("li.dragged"), jQuery(event.target), mov)) {
						if(mov == "inside")	jQuery("#marker").attr("src", _this.settings.ui.theme_path + "default/plus.gif").width(14);
						else {
							if(cnt.hasClass("rtl"))	{ jQuery("#marker").attr("src", _this.settings.ui.theme_path + "default/marker_rtl.gif").width(40); }
							else					{ jQuery("#marker").attr("src", _this.settings.ui.theme_path + "default/marker.gif").width(40); }
						}
						_this.moveType	= mov;
						_this.moveRef	= event.target;
						jQuery(_this.drag).children("IMG").remove();
						jQuery("#marker").css({ "left" : goTo.x-1 , "top" : goTo.y-2 }).show();
					}
					else {
						if(jQuery(_this.drag).children("IMG").size() == 0) {
							jQuery(_this.drag).append("<img class='removeicon' style='position:absolute; " + (_this.settings.ui.rtl ? "right:0px;" : "left:4px;" ) + " top:0px;' src='" + _this.settings.ui.theme_path + "default/remove.gif' />");
						}
						_this.moveType = false;
						_this.moveRef = false;
						jQuery("#marker").hide();
					}
				}
				else {
					if(jQuery(_this.drag).children("IMG").size() == 0) {
						jQuery(_this.drag).append("<img class='removeicon' style='position:absolute; " + (_this.settings.ui.rtl ? "right:0px;" : "left:4px;" ) + " top:0px;' src='" + _this.settings.ui.theme_path + "default/remove.gif' />");
					}
					_this.moveType = false;
					_this.moveRef = false;
					jQuery("#marker").hide();
				}
				event.preventDefault();
				event.stopPropagation();
				return false;
			}
			return true;
		};
	}
	return {
		cntr : tree_component.cntr ++,
		settings : {
			data	: {
				type	: "predefined",	// ENUM [json, xml_flat, xml_nested, predefined]
				method	: "GET",		// HOW TO REQUEST FILES
				async	: false,		// BOOL - async loading onopen
				async_data : function (NODE) { return { id : jQuery(NODE).attr("id") || 0 } }, // PARAMETERS PASSED TO SERVER
				url		: false,		// FALSE or STRING - url to document to be used (async or not)
				json	: false			// FALSE or OBJECT if type is JSON and async is false - the tree dump as json
			},
			selected	: false,		// FALSE or STRING or ARRAY
			opened		: [],			// ARRAY OF INITIALLY OPENED NODES
			languages	: [],			// ARRAY of string values (which will be used as CSS classes - si they must be valid)
			path		: false,		// FALSE or STRING (if false - will be autodetected)
			cookies		: false,		// FALSE or OBJECT (prefix, opts - from jqCookie - expires, path, domain, secure)
			ui		: {
				dots		: true,		// BOOL - dots or no dots
				rtl			: false,	// BOOL - is the tree right-to-left
				animation	: 0,		// INT - duration of open/close animations in miliseconds
				hover_mode	: true,		// SHOULD get_* functions chage focus or change hovered item
				scroll_spd	: 4,
				theme_path	: false,	// Path to themes
				theme_name	: "default",// Name of theme
				context		: [ 
					{
						id		: "create",
						label	: "Create", 
						icon	: "create.png",
						visible	: function (NODE, TREE_OBJ) { if(NODE.length != 1) return false; return TREE_OBJ.check("creatable", NODE); }, 
						action	: function (NODE, TREE_OBJ) { TREE_OBJ.create(false, NODE); } 
					},
					"separator",
					{ 
						id		: "rename",
						label	: "Rename", 
						icon	: "rename.png",
						visible	: function (NODE, TREE_OBJ) { if(NODE.length != 1) return false; return TREE_OBJ.check("renameable", NODE); }, 
						action	: function (NODE, TREE_OBJ) { TREE_OBJ.rename(); } 
					},
					{ 
						id		: "delete",
						label	: "Delete",
						icon	: "remove.gif",
						visible	: function (NODE, TREE_OBJ) { return TREE_OBJ.check("deletable", NODE); }, 
						action	: function (NODE, TREE_OBJ) { NODE.each( function () { TREE_OBJ.remove(this); }); } 
					}
				]
			},
			rules	: {
				multiple	: false,	// FALSE | CTRL | ON - multiple selection off/ with or without holding Ctrl
				metadata	: false,	// FALSE or STRING - attribute name (use metadata plugin)
				type_attr	: "rel",	// STRING attribute name (where is the type stored if no metadata)
				multitree	: false,	// BOOL - is drag n drop between trees allowed
				createat	: "bottom",	// STRING (top or bottom) new nodes get inserted at top or bottom
				use_inline	: false,	// CHECK FOR INLINE RULES - REQUIRES METADATA
				clickable	: "all",	// which node types can the user select | default - all
				renameable	: "all",	// which node types can the user select | default - all
				deletable	: "all",	// which node types can the user delete | default - all
				creatable	: "all",	// which node types can the user create in | default - all
				draggable	: "none",	// which node types can the user move | default - none | "all"
				dragrules	: "all",	// what move operations between nodes are allowed | default - none | "all"
				drag_copy	: false,	// FALSE | CTRL | ON - drag to copy off/ with or without holding Ctrl
				droppable	: []
			},
			lang : {
				new_node	: "New folder",
				loading		: "Loading ..."
			},
			callback	: {				// various callbacks to attach custom logic to
				// before focus  - should return true | false
				beforechange: function(NODE,TREE_OBJ) { return true },
				// before move   - should return true | false
				beforemove  : function(NODE,REF_NODE,TYPE,TREE_OBJ) { return true }, 
				// before create - should return true | false
				beforecreate: function(NODE,REF_NODE,TYPE,TREE_OBJ) { return true }, 
				// before rename - should return true | false
				beforerename: function(NODE,LANG,TREE_OBJ) { return true }, 
				// before delete - should return true | false
				beforedelete: function(NODE,TREE_OBJ) { return true }, 

				onchange	: function(NODE,TREE_OBJ) { },					// focus changed
				onrename	: function(NODE,LANG,TREE_OBJ) { },				// node renamed ISNEW - TRUE|FALSE, current language
				onmove		: function(NODE,REF_NODE,TYPE,TREE_OBJ) { },	// move completed (TYPE is BELOW|ABOVE|INSIDE)
				oncopy		: function(NODE,REF_NODE,TYPE,TREE_OBJ) { },	// copy completed (TYPE is BELOW|ABOVE|INSIDE)
				oncreate	: function(NODE,REF_NODE,TYPE,TREE_OBJ) { },	// node created, parent node (TYPE is insertAt)
				ondelete	: function(NODE, TREE_OBJ) { },					// node deleted
				onopen		: function(NODE, TREE_OBJ) { },					// node opened
				onclose		: function(NODE, TREE_OBJ) { },					// node closed
				error		: function(TEXT, TREE_OBJ) { },					// error occured
				// double click on node - defaults to open/close & select
				ondblclk	: function(NODE, TREE_OBJ) { TREE_OBJ.toggle_branch.call(TREE_OBJ, NODE); TREE_OBJ.select_branch.call(TREE_OBJ, NODE); },
				// right click - to prevent use: EV.preventDefault(); EV.stopPropagation(); return false
				onrgtclk	: function(NODE, TREE_OBJ, EV) { },
				onload		: function(TREE_OBJ) { },
				onfocus		: function(TREE_OBJ) { },
				ondrop		: function(NODE,REF_NODE,TYPE,TREE_OBJ) {}
			}
		},
		// INITIALIZATION
		init : function(elem, opts) {
			var _this = this;
			this.container		= jQuery(elem);
			if(this.container.size == 0) { alert("Invalid container node!"); return }

			tree_component.inst[this.cntr] = this;
			if(!this.container.attr("id")) this.container.attr("id","jstree_" + this.cntr); 
			tree_component.inst[this.container.attr("id")] = tree_component.inst[this.cntr];
			tree_component.focused = this.cntr;

			// MERGE OPTIONS WITH DEFAULTS
			if(opts && opts.cookies) {
				this.settings.cookies = jQuery.extend({},this.settings.cookies,opts.cookies);
				delete opts.cookies;
				if(!this.settings.cookies.opts) this.settings.cookies.opts = {};
			}
			if(opts && opts.callback) {
				this.settings.callback = jQuery.extend({},this.settings.callback,opts.callback);
				delete opts.callback;
			}
			if(opts && opts.data) {
				this.settings.data = jQuery.extend({},this.settings.data,opts.data);
				delete opts.data;
			}
			if(opts && opts.ui) {
				this.settings.ui = jQuery.extend({},this.settings.ui,opts.ui);
				delete opts.ui;
			}
			if(opts && opts.rules) {
				this.settings.rules = jQuery.extend({},this.settings.rules,opts.rules);
				delete opts.rules;
			}
			if(opts && opts.lang) {
				this.settings.lang = jQuery.extend({},this.settings.lang,opts.lang);
				delete opts.lang;
			}
			this.settings		= jQuery.extend({},this.settings,opts);

			// PATH TO IMAGES AND XSL
			if(this.settings.path == false) {
				this.path = "";
				jQuery("script").each( function () { 
					if(this.src.toString().match(/tree_component.*?js$/)) {
						_this.path = this.src.toString().replace(/tree_component.*?js$/, "");
					}
				});
			}
			else this.path = this.settings.path;

			// DEAL WITH LANGUAGE VERSIONS
			this.current_lang	= this.settings.languages && this.settings.languages.length ? this.settings.languages[0] : false;
			if(this.settings.languages && this.settings.languages.length) {
				this.sn = get_sheet_num("tree_component.css");
				var st = false;
				var id = this.container.attr("id") ? "#" + this.container.attr("id") : ".tree";
				for(var ln = 0; ln < this.settings.languages.length; ln++) {
					st = add_css(id + " ." + this.settings.languages[ln], this.sn);
					if(st !== false) {
						if(this.settings.languages[ln] == this.current_lang)	st.style.display = "inline";
						else													st.style.display = "none";
					}
				}
			}

			// DROPPABLES 
			if(this.settings.rules.droppable.length) {
				for(i in this.settings.rules.droppable) {
					tree_component.drop.push(this.settings.rules.droppable[i]);
					tree_component.drop = jQuery.unique(tree_component.drop);
				}
			}

			// THEMES
			if(this.settings.ui.theme_path === false) this.settings.ui.theme_path = this.path + "themes/";
			this.theme = this.settings.ui.theme_path + _this.settings.ui.theme_name + "/";
			add_sheet(_this.settings.ui.theme_path + "default/style.css");
			if(this.settings.ui.theme_name != "default") add_sheet(_this.theme + "style.css");

			this.container.addClass("tree");
			if(this.settings.ui.rtl) this.container.addClass("rtl");
			if(this.settings.rules.multiple) this.selected_arr = [];
			this.offset = false;

			if(this.settings.ui.dots == false) this.container.addClass("no_dots");

			// CONTEXT MENU
			this.context = false;
			if(this.settings.ui.context != false) {
				var str = '<div class="context">';
				for(i in this.settings.ui.context) {
					if(this.settings.ui.context[i] == "separator") {
						str += "<span class='separator'>&nbsp;</span>";
						continue;
					}
					var icn = "";
					if(this.settings.ui.context[i].icon) icn = 'background-image:url(\'' + ( this.settings.ui.context[i].icon.indexOf("/") == -1 ? this.theme + this.settings.ui.context[i].icon : this.settings.ui.context[i].icon ) + '\');';
					str += '<a rel="' + this.settings.ui.context[i].id + '" href="#" style="' + icn + '">' + this.settings.ui.context[i].label + '</a>';
				}
				str += '</div>';
				this.context = jQuery(str);
				this.context.hide();
				this.context.append = false;
			}

			this.hovered = false;
			this.locked = false;

			// CREATE DUMMY FOR MOVING
			if(this.settings.rules.draggable != "none" && this.settings.rules.dragrules != "none") {
				var _this = this;
				jQuery("<img>")
					.attr({
						id		: "marker", 
						src	: _this.settings.ui.theme_path + "default/marker.gif"
					})
					.css({
						height		: "8px",
						width		: "42px",
						display		: "block",
						position	: "absolute",
						left		: "30px",
						top			: "30px",
						zIndex		: "1000"
					}).hide().appendTo("body");
			}
			this.refresh();
			this.attachEvents();
			this.focus();
		},
		off_height : function () {
			if(this.offset === false) {
				this.container.css({ position : "relative" });
				this.offset = this.container.offset();
				var tmp = 0;
				tmp = parseInt(jQuery.curCSS(this.container.get(0), "paddingTop", true),10);
				if(tmp) this.offset.top += tmp;
				tmp = parseInt(jQuery.curCSS(this.container.get(0), "borderTopWidth", true),10);
				if(tmp) this.offset.top += tmp;
				this.container.css({ position : "" });
			}
			if(!this.li_height) {
				var tmp = this.container.find("ul li:eq(0)");
				this.li_height = tmp.height();
				if(tmp.children("ul:eq(0)").size()) this.li_height -= tmp.children("ul:eq(0)").height();
				if(!this.li_height) this.li_height = 18;
			}
		},
		// REPAINT TREE
		refresh : function (obj) {
			if(this.locked) return this.error("LOCKED");
			var _this = this;

			// SAVE OPENED
			this.opened = Array();
			if(this.settings.cookies && jQuery.cookie(this.settings.cookies.prefix + '_open')) {
				var str = jQuery.cookie(this.settings.cookies.prefix + '_open');
				var tmp = str.split(",");
				jQuery.each(tmp, function () {
					_this.opened.push("#" + this.replace(/^#/,""));
				});
				this.settings.opened = false;
			}
			else if(this.settings.opened != false) {
				jQuery.each(this.settings.opened, function (i, item) {
					_this.opened.push("#" + this.replace(/^#/,""));
				});
				this.settings.opened = false;
			}
			else {
				this.container.find("li.open").each(function (i) { _this.opened.push("#" + this.id); });
			}

			// SAVE SELECTED
			if(this.selected) {
				this.settings.selected = Array();
				if(this.selected_arr) {
					jQuery.each(this.selected_arr, function () {
						_this.settings.selected.push("#" + this.attr("id"));
					});
				}
				else this.settings.selected.push("#" + this.selected.attr("id"));
			}
			/*else if(this.settings.cookies && jQuery.cookie(this.settings.cookies.prefix + '_selected')) {
				this.settings.selected = Array();
				var str = jQuery.cookie(this.settings.cookies.prefix + '_selected');
				var tmp = str.split(",");
				jQuery.each(tmp, function () {
					_this.settings.selected.push("#" + this.replace(/^#/,""));
				});
			}*/
			else if(this.settings.selected !== false) {
				var tmp = Array();
				if((typeof this.settings.selected).toLowerCase() == "object") {
					jQuery.each(this.settings.selected, function () {
						tmp.push("#" + this.replace(/^#/,""));
					});
				}
				else tmp.push("#" + this.settings.selected.replace(/^#/,""));
				this.settings.selected = tmp;
			}

			if(obj && this.settings.data.async) {
				this.opened = Array();
				obj = this.get_node(obj);
				obj.find("li.open").each(function (i) { _this.opened.push("#" + this.id); });
				this.close_branch(obj, true);
				obj.children("ul:eq(0)").html("");
				return this.open_branch(obj, true, function () { _this.reselect.apply(_this); });
			}

			var cls = "tree-default";
			if(this.settings.ui.theme_name != "default") cls += " tree-" + _this.settings.ui.theme_name;

			if(this.settings.data.type == "xml_flat" || this.settings.data.type == "xml_nested") {
				this.scrtop = this.container.get(0).scrollTop;
				var xsl = (this.settings.data.type == "xml_flat") ? "flat.xsl" : "nested.xsl";
				this.container.getTransform(this.path + xsl, this.settings.data.url, { params : { theme_name : cls, theme_path : _this.theme }, meth : _this.settings.data.method ,callback: function () { _this.reselect.apply(_this); } });
				return;
			}
			else if(this.settings.data.type == "json") {
				if(this.settings.data.json) {
					var str = "";
					if(this.settings.data.json.length) {
						for(var i = 0; i < this.settings.data.json.length; i++) {
							str += this.parseJSON(this.settings.data.json[i]);
						}
					} else str = this.parseJSON(this.settings.data.json);
					this.container.html("<ul class='" + cls + "'>" + str + "</ul>");
					this.container.find("li:last-child").addClass("last").end().find("li:has(ul)").not(".open").addClass("closed");
					this.container.find("li").not(".open").not(".closed").addClass("leaf");
					this.reselect();
				}
				else {
					var _this = this;
					jQuery.ajax({
						type		: this.settings.data.method,
						url			: this.settings.data.url, 
						data		: this.settings.data.async_data(false), 
						dataType	: "json",
						success		: function (data) {
							var str = "";
							if(data.length) {
								for(var i = 0; i < data.length; i++) {
									str += _this.parseJSON(data[i]);
								}
							} else str = _this.parseJSON(data);
							_this.container.html("<ul class='" + cls + "'>" + str + "</ul>");
							_this.container.find("li:last-child").addClass("last").end().find("li:has(ul)").not(".open").addClass("closed");
							_this.container.find("li").not(".open").not(".closed").addClass("leaf");
							_this.reselect.apply(_this);
						} 
					});
				}
			}
			else {
				this.container.children("ul:eq(0)").attr("class", cls);
				this.container.find("li:last-child").addClass("last").end().find("li:has(ul)").not(".open").addClass("closed");
				this.container.find("li").not(".open").not(".closed").addClass("leaf");
				this.reselect();
			}
		},
		// CONVERT JSON TO HTML
		parseJSON : function (data) {
			var str = "";
			str += "<li ";
			var cls = false;
			for(i in data.attributes) {
				if(i == "class") {
					str += " class='" + data.attributes[i] + " ";
					if(data.state == "closed" || data.state == "open") str += " " + data.state + " ";
					str += "' ";
					cls = true;
				}
				else str += " " + i + "='" + data.attributes[i] + "' ";
			}
			if(!cls && (data.state == "closed" || data.state == "open")) str += " class='" + data.state + "' ";
			str += ">";
			if(this.settings.languages.length) {
				for(var i = 0; i < this.settings.languages.length; i++) {
					var attr = [];
					attr["href"] = "#";
					attr["style"] = "";
					attr["class"] = this.settings.languages[i];
					if(data.data[this.settings.languages[i]] && (typeof data.data[this.settings.languages[i]].attributes).toLowerCase() != "undefined") {
						for(j in data.data[this.settings.languages[i]].attributes) {
							if(j == "style" || j == "class")	attr[j] += " " + data.data[this.settings.languages[i]].attributes[j];
							else								attr[j]  = data.data[this.settings.languages[i]].attributes[j];
						}
					}
					if(data.data[this.settings.languages[i]] && data.data[this.settings.languages[i]].icon) {
						var icn = data.data[this.settings.languages[i]].icon.indexOf("/") == -1 ? this.theme + data.data[this.settings.languages[i]].icon : data.data[this.settings.languages[i]].icon;
						attr["style"] += " ; background-image:url('" + icn + "'); ";
					}
					str += "<a";
					for(j in attr) str += ' ' + j + '="' + attr[j] + '" ';
					str += ">" + ( (typeof data.data[this.settings.languages[i]].title).toLowerCase() != "undefined" ? data.data[this.settings.languages[i]].title : data.data[this.settings.languages[i]] ) + "</a>";
				}
			}
			else {
				var attr = [];
				attr["href"] = "#";
				attr["style"] = "";
				attr["class"] = "";
				if((typeof data.data.attributes).toLowerCase() != "undefined") {
					for(i in data.data.attributes) {
						if(i == "style" || i == "class")	attr[i] += " " + data.data.attributes[i];
						else								attr[i]  = data.data.attributes[i];
					}
				}
				if(data.data.icon) {
					var icn = data.data.icon.indexOf("/") == -1 ? this.theme + data.data.icon : data.data.icon;
					attr["style"] += " ; background-image:url('" + icn + "');";
				}
				str += "<a";
				for(i in attr) str += ' ' + i + '="' + attr[i] + '" ';
				str += ">" + ( (typeof data.data.title).toLowerCase() != "undefined" ? data.data.title : data.data ) + "</a>";
			}
			if(data.children && data.children.length) {
				str += '<ul>';
				for(var i = 0; i < data.children.length; i++) {
					str += this.parseJSON(data.children[i]);
				}
				str += '</ul>';
			}
			str += "</li>";
			return str;
		},
		// getJSON from HTML
		getJSON : function (nod, outer_attrib, inner_attrib, force) {
			var _this = this;
			if(!nod || jQuery(nod).size() == 0) {
				nod = this.container.children("ul").children("li");
			}
			else nod = jQuery(nod);

			if(nod.size() > 1) {
				var arr = [];
				nod.each(function () {
					arr.push(_this.getJSON(this, outer_attrib, inner_attrib));
				});
				return arr;
			}

			if(!outer_attrib) outer_attrib = [ "id", "rel", "class" ];
			if(!inner_attrib) inner_attrib = [ ];
			var obj = { attributes : {}, data : false };
			for(i in outer_attrib) {
				obj.attributes[outer_attrib[i]] = nod.attr(outer_attrib[i]);
			}
			if(this.settings.languages.length) {
				obj.data = {};
				for(i in this.settings.languages) {
					var a = nod.children("a." + this.settings.languages[i]);
					if(force || inner_attrib.length || a.get(0).style.backgroundImage.toString().length) {
						obj.data[this.settings.languages[i]] = {};
						obj.data[this.settings.languages[i]].title = a.text();
						if(a.get(0).style.backgroundImage.length) {
							obj.data[this.settings.languages[i]].icon = a.get(0).style.backgroundImage.replace("url(","").replace(")","");
						}
						if(inner_attrib.length) {
							obj.data[this.settings.languages[i]].attributes = {};
							for(j in inner_attrib) {
								obj.data[this.settings.languages[i]].attributes[inner_attrib[j]] = a.attr(inner_attrib[j]);
							}
						}
					}
					else {
						obj.data[this.settings.languages[i]] = a.text();
					}
				}
			}
			else {
				var a = nod.children("a");
				if(force || inner_attrib.length || a.get(0).style.backgroundImage.toString().length) {
					obj.data = {};
					obj.data.title = a.text();
					if(a.get(0).style.backgroundImage.length) {
						obj.data.icon = a.get(0).style.backgroundImage.replace("url(","").replace(")","");
					}
					if(inner_attrib.length) {
						obj.data.attributes = {};
						for(j in inner_attrib) {
							obj.data.attributes[inner_attrib[j]] = a.attr(inner_attrib[j]);
						}
					}
				}
				else {
					obj.data = a.text();
				}
			}

			if(nod.children("ul").size() > 0) {
				obj.children = [];
				nod.children("ul").children("li").each(function () {
					obj.children.push(_this.getJSON(this, outer_attrib, inner_attrib));
				});
			}
			return obj;
		},
		focus : function () {
			if(this.locked) return false;
			if(tree_component.focused != this.cntr) {
				tree_component.focused = this.cntr;
				this.settings.callback.onfocus.call(null, this);
			}
		},
		show_context : function (obj, x, y) {
			var tmp = this.context.show().offsetParent();
			if(tmp.is("html")) tmp = jQuery("body");
			tmp = tmp.offset();
			this.context.css({ "left" : (x - tmp.left - (this.settings.ui.rtl ? jQuery(this.context).width() : -5 ) ), "top" : (y - tmp.top  + (jQuery.browser.opera ? this.container.scrollTop() : 0) + 15) });
		},
		hide_context : function () {
			this.context.hide();
		},
		// ALL EVENTS
		attachEvents : function () {
			var _this = this;

			this.container
				.bind("mouseup", function (event) {
					setTimeout( function() { _this.focus.apply(_this); }, 5);
				})
				.bind("click", function (event) { 
					event.stopPropagation(); 
					return true;
				})
				.listen("click", "li", function(event) { // WHEN CLICK IS ON THE ARROW
					_this.toggle_branch.apply(_this, [event.target]);
					event.stopPropagation();
				})
				.listen("click", "a.title", function (event) { // WHEN CLICK IS ON THE TEXT OR ICON
					if(_this.locked) {
						event.preventDefault(); 
						event.target.blur();
						return _this.error("LOCKED");
					}
					_this.select_branch.apply(_this, [event.target, event.ctrlKey || _this.settings.rules.multiple == "on"]);
					if(_this.inp) { _this.inp.blur(); }
					event.preventDefault(); 
					event.target.blur();
					return false;
				})
				.listen("dblclick", "a.title", function (event) { // WHEN DOUBLECLICK ON TEXT OR ICON
					if(_this.locked) {
						event.preventDefault(); 
						event.stopPropagation();
						event.target.blur();
						return _this.error("LOCKED");
					}
					_this.settings.callback.ondblclk.call(null, _this.get_node(event.target).get(0), _this);
					event.preventDefault(); 
					event.stopPropagation();
					event.target.blur();
				})
				.listen("contextmenu", "a.title", function (event) {
					if(_this.locked) {
						event.target.blur();
						return _this.error("LOCKED");
					}
					_this.settings.callback.onrgtclk.call(null, _this.get_node(event.target).get(0), _this, event);
					if(_this.context) {
						if(_this.context.append == false) {
							_this.container.find("ul:eq(0)").append(_this.context);
							_this.context.append = true;
							for(i in _this.settings.ui.context) {
								if(_this.settings.ui.context[i] == "separator") continue;
								(function () {
									var func = _this.settings.ui.context[i].action;
									_this.context.children("[rel=" + _this.settings.ui.context[i].id +"]").bind("click", function (event) {
										func.call(null, _this.selected_arr || _this.selected, _this);
										_this.hide_context();
										event.stopPropagation();
										event.preventDefault();
										return false;
									});
								})();
							}
						}
						var obj = _this.get_node(event.target);
						if(_this.inp) { _this.inp.blur(); }
						if(obj) {
							if(!obj.children("a:eq(0)").hasClass("clicked")) {
								_this.select_branch.apply(_this, [event.target, event.ctrlKey || _this.settings.rules.multiple == "on"]);
								event.target.blur();
							}
							_this.context.children("li").show();
							var go = false;
							for(i in _this.settings.ui.context) {
								if(_this.settings.ui.context[i] == "separator") continue;
								if(!_this.settings.ui.context[i].visible.call(null, _this.selected_arr || _this.selected, _this)) _this.context.children("[rel=" + _this.settings.ui.context[i].id +"]").hide();
								else go = true;
							}
							if(go == true) _this.show_context(obj, event.pageX, event.pageY);
							event.preventDefault(); 
							event.stopPropagation(); 
							return false;
						}
					}
					return true;
				})
				.listen("mouseover", "a.title", function (event) {
					if(_this.locked) {
						event.preventDefault();
						event.stopPropagation();
						return _this.error("LOCKED");
					}
					if(_this.settings.ui.hover_mode && _this.hovered !== false && event.target.tagName == "A") {
						_this.hovered.children("a").removeClass("hover");
						_this.hovered = false;
					}
				});

				// ATTACH DRAG & DROP ONLY IF NEEDED
				if(this.settings.rules.draggable != "none" && this.settings.rules.dragrules != "none") {
					this.container
						.listen("mousedown", "a", function (event) {
							_this.focus.apply(_this);
							if(_this.locked) return _this.error("LOCKED");
							// SELECT LIST ITEM NODE
							var obj = _this.get_node(event.target);
							// IF ITEM IS DRAGGABLE
							if(_this.settings.rules.multiple != false && _this.selected_arr.length > 1 && obj.children("a:eq(0)").hasClass("clicked")) {
								var counter = 0;
								for(i in _this.selected_arr) {
									if(_this.check("draggable", _this.selected_arr[i])) {
										_this.selected_arr[i].addClass("dragged");
										counter ++;
									}
								}
								if(counter > 0) {
									if(_this.check("draggable", obj))	_this._drag = obj;
									else								_this._drag = _this.container.find("li.dragged:eq(0)");
									_this.isdown	= true;
									_this.drag		= _this._drag.get(0).cloneNode(true);
									_this.drag.id	= "dragged";
									jQuery(_this.drag).children("a").html("Multiple selection").end().children("ul").remove();
								}
							}
							else {
								if(_this.check("draggable", obj)) {
									_this._drag		= obj;
									_this.drag		= obj.get(0).cloneNode(true);
									_this.drag.id	= "dragged";
									_this.isdown	= true;
									_this.foreign	= false;
									obj.addClass("dragged");
								}
							}
							obj.blur();
							event.preventDefault(); 
							event.stopPropagation();
							return false;
						});
					jQuery(document)
						.bind("mousedown",	tree_component.mousedown)
						.bind("mouseup",	tree_component.mouseup)
						.bind("mousemove",	tree_component.mousemove);
				} 
				// ENDIF OF DRAG & DROP FUNCTIONS
			if(_this.context) jQuery(document).bind("mouseup", function() { _this.hide_context(); });
		},
		checkMove : function (NODES, REF_NODE, TYPE) {
			if(this.locked) return this.error("LOCKED");
			var _this = this;
			// OVER SELF OR CHILDREN
			if(REF_NODE.parents("li.dragged").size() > 0 || REF_NODE.is(".dragged")) return this.error("MOVE: NODE OVER SELF");
			// CHECK AGAINST DRAG_RULES
			if(NODES.size() == 1) {
				var NODE = NODES.eq(0);
				if(NODE.hasClass("foreign")) {
					if(this.settings.rules.droppable.length == 0) return false;
					if(!NODE.is("." + this.settings.rules.droppable.join(", ."))) return false;
					var ok = false;
					for(i in this.settings.rules.droppable) {
						if(NODE.is("." + this.settings.rules.droppable[i])) {
							if(this.settings.rules.metadata) {
								jQuery.metadata.setType("attr", this.settings.rules.metadata);
								NODE.attr(this.settings.rules.metadata, "type: '" + this.settings.rules.droppable[i] + "'");
							}
							else {
								NODE.attr(this.settings.rules.type_attr, this.settings.rules.droppable[i]);
							}
							ok = true;
							break;
						}
					}
					if(!ok) return false;
				}
				if(!this.check("dragrules", [NODE, TYPE, REF_NODE.parents("li:eq(0)")])) return this.error("MOVE: AGAINST DRAG RULES");
			}
			else {
				var ok = true;
				NODES.each(function (i) {
					if(ok == false) return false;
					if(i > 0) {
						var ref = NODES.eq( (i - 1) );
						var mv = "after";
					}
					else {
						var ref = REF_NODE;
						var mv = TYPE;
					}
					if(!_this.check.apply(_this,["dragrules", [jQuery(this), mv, ref]])) ok = false;
				});
				if(ok == false) return this.error("MOVE: AGAINST DRAG RULES");
			}
			// CHECK AGAINST METADATA
			if(this.settings.rules.use_inline && this.settings.rules.metadata) {
				var nd = false;
				if(TYPE == "inside")	nd = REF_NODE.parents("li:eq(0)");
				else					nd = REF_NODE.parents("li:eq(1)");
				if(nd.size()) {
					// VALID CHILDREN CHECK
					if(typeof nd.metadata()["valid_children"] != "undefined") {
						var tmp = nd.metadata()["valid_children"];
						var ok = true;
						NODES.each(function (i) {
							if(ok == false) return false;
							if(jQuery.inArray(_this.get_type(this), tmp) == -1) ok = false;
						});
						if(ok == false) return this.error("MOVE: NOT A VALID CHILD");
					}
					// CHECK IF PARENT HAS FREE SLOTS FOR CHILDREN
					if(typeof nd.metadata()["max_children"] != "undefined") {
						if((nd.children("ul:eq(0)").children("li").not(".dragged").size() + NODES.size()) > nd.metadata().max_children) return this.error("MOVE: MAX CHILDREN REACHED");
					}
					// CHECK FOR MAXDEPTH UP THE CHAIN
					var incr = 0;
					NODES.each(function (i) {
						var i = 1;
						var t = jQuery(this);
						while(i < 100) {
							t = t.children("ul:eq(0)");
							if(t.size() == 0) break;
							i ++
						}
						incr = Math.max(i,incr);
					});
					var ok = true;
					nd.parents("li").each(function(i) {
						if(ok == false) return false;
						if(jQuery(this).metadata().max_depth) {
							if( (i + incr) >= jQuery(this).metadata().max_depth) ok = false;
						}
					});
					if(ok == false) return this.error("MOVE: MAX_DEPTH REACHED");
				}
			}
			return true;
		},
		// USED AFTER REFRESH
		reselect : function () {
			var _this = this;
			// REOPEN BRANCHES
			if(this.opened && this.opened.length) {
				var opn = false;
				for(var j = 0; j < this.opened.length; j++) {
					if(this.settings.data.async) {
						if(this.get_node(this.opened[j]).size() > 0) {
							opn = true;
							var tmp = this.opened[j];
							delete this.opened[j];
							this.open_branch(tmp, true, function () { _this.reselect.apply(_this); } )
						}
					}
					else this.open_branch(this.opened[j], true);
				}
				if(this.settings.data.async && opn) return;
				delete this.opened;
			}
			// REPOSITION SCROLL
			if(this.scrtop) {
				this.container.scrollTop(_this.scrtop);
				delete this.scrtop;
			}
			// RESELECT PREVIOUSLY SELECTED
			if(this.settings.selected !== false) {
				jQuery.each(this.settings.selected, function (i) {
					_this.select_branch(jQuery(_this.settings.selected[i]), (_this.settings.rules.multiple !== false && i > 0) );
				});
				this.settings.selected = false;
			}
			this.settings.callback.onload.call(null, _this);
		},
		// GET THE EXTENDED LI ELEMENT
		get_node : function (obj) {
			var obj = jQuery(obj);
			return obj.is("li") ? obj : obj.parents("li:eq(0)");
		},
		// GET THE TYPE OF THE NODE
		get_type : function (obj) {
			obj = !obj ? this.selected : this.get_node(obj);
			if(!obj) return;
			if(this.settings.rules.metadata) {
				jQuery.metadata.setType("attr", this.settings.rules.metadata);
				var tmp = obj.metadata().type;
				if(tmp) return tmp;
			} 
			return obj.attr(this.settings.rules.type_attr);
		},
		// SCROLL CONTAINER WHILE DRAGGING
		scrollCheck : function (x,y) { 
			var _this = this;
			var cnt = _this.container;
			var off = _this.offset;

			var st = cnt.scrollTop();
			var sl = cnt.scrollLeft();
			// DETECT HORIZONTAL SCROLL
			var h_cor = (cnt.get(0).scrollWidth > cnt.width()) ? 40 : 20;

			if(y - off.top < 20)						cnt.scrollTop(Math.max( (st - _this.settings.ui.scroll_spd) ,0));	// NEAR TOP
			if(cnt.height() - (y - off.top) < h_cor)	cnt.scrollTop(st + _this.settings.ui.scroll_spd);					// NEAR BOTTOM
			if(x - off.left < 20)						cnt.scrollLeft(Math.max( (sl - _this.settings.ui.scroll_spd),0));	// NEAR LEFT
			if(cnt.width() - (x - off.left) < 40)		cnt.scrollLeft(sl + _this.settings.ui.scroll_spd);					// NEAR RIGHT

			if(cnt.scrollLeft() != sl || cnt.scrollTop() != st) {
				_this.moveType = false;
				_this.moveRef = false;
				jQuery("#marker").hide();
			}
			tree_component.sto = setTimeout( function() { _this.scrollCheck(x,y); }, 50);
		},
		check : function (rule, nodes) {
			if(this.locked) return this.error("LOCKED");
			// CHECK LOCAL RULES IF METADATA
			if(rule != "dragrules" && this.settings.rules.use_inline && this.settings.rules.metadata) {
				jQuery.metadata.setType("attr", this.settings.rules.metadata);
				if(typeof this.get_node(nodes).metadata()[rule] != "undefined") return this.get_node(nodes).metadata()[rule];
			}
			if(!this.settings.rules[rule])			return false;
			if(this.settings.rules[rule] == "none")	return false;
			if(this.settings.rules[rule] == "all")	return true;
			if(rule == "dragrules") {
				var nds = new Array();
				nds[0] = this.get_type(nodes[0]);
				nds[1] = nodes[1];
				nds[2] = this.get_type(nodes[2]);
				for(var i = 0; i < this.settings.rules.dragrules.length; i++) {
					var r = this.settings.rules.dragrules[i];
					var n = (r.indexOf("!") === 0) ? false : true;
					if(!n) r = r.replace("!","");
					var tmp = r.split(" ");
					for(var j = 0; j < 3; j++) {
						if(tmp[j] == nds[j] || tmp[j] == "*") tmp[j] = true;
					}
					if(tmp[0] === true && tmp[1] === true && tmp[2] === true) return n;
				}
				return false;
			}
			else 
				return (jQuery.inArray(this.get_type(nodes),this.settings.rules[rule]) != -1) ? true : false;
		},
		hover_branch : function (obj) {
			if(this.locked) return this.error("LOCKED");
			if(this.settings.ui.hover_mode == false) return this.select_branch(obj);
			var _this = this;
			var obj = _this.get_node(obj);
			if(!obj.size()) return this.error("HOVER: NOT A VALID NODE");
			// CHECK AGAINST RULES FOR SELECTABLE NODES
			if(!_this.check("clickable", obj)) return this.error("SELECT: NODE NOT SELECTABLE");
			if(this.hovered) this.hovered.children("A").removeClass("hover");

			// SAVE NEWLY SELECTED
			this.hovered = obj;

			// FOCUS NEW NODE AND OPEN ALL PARENT NODES IF CLOSED
			this.hovered.children("a").removeClass("hover").addClass("hover");

			// SCROLL SELECTED NODE INTO VIEW
			var off_t = this.hovered.offset().top;
			var beg_t = this.container.offset().top;
			var end_t = beg_t + this.container.height();
			var h_cor = (this.container.get(0).scrollWidth > this.container.width()) ? 40 : 20;
			if(off_t + 5 < beg_t) this.container.scrollTop(this.container.scrollTop() - (beg_t - off_t + 5) );
			if(off_t + h_cor > end_t) this.container.scrollTop(this.container.scrollTop() + (off_t + h_cor - end_t) );
		},
		select_branch : function (obj, multiple) {
			if(this.locked) return this.error("LOCKED");
			if(!obj && this.hovered !== false) obj = this.hovered;
			var _this = this;
			obj = _this.get_node(obj);
			if(!obj.size()) return this.error("SELECT: NOT A VALID NODE");
			obj.children("a").removeClass("hover");
			// CHECK AGAINST RULES FOR SELECTABLE NODES
			if(!_this.check("clickable", obj)) return this.error("SELECT: NODE NOT SELECTABLE");
			if(_this.settings.callback.beforechange.call(null,obj.get(0),_this) === false) return this.error("SELECT: STOPPED BY USER");
			// IF multiple AND obj IS ALREADY SELECTED - DESELECT IT
			if(this.settings.rules.multiple != false && multiple && obj.children("a.clicked").size() > 0) {
				return this.deselect_branch(obj);
			}
			if(this.settings.rules.multiple != false && multiple) {
				this.selected_arr.push(obj);
			}
			if(this.settings.rules.multiple != false && !multiple) {
				for(i in this.selected_arr) {
					this.selected_arr[i].children("A").removeClass("clicked");
				}
				this.selected_arr = [];
				this.selected_arr.push(obj);
				if(this.selected) this.selected.children("A").removeClass("clicked");
			}
			if(!this.settings.rules.multiple) {
				if(this.selected) this.selected.children("A").removeClass("clicked");
			}
			// SAVE NEWLY SELECTED
			this.selected = obj;
			if(this.settings.ui.hover_mode && this.hovered !== false) {
				this.hovered.children("A").removeClass("hover");
				this.hovered = obj;
			}

			// FOCUS NEW NODE AND OPEN ALL PARENT NODES IF CLOSED
			this.selected.children("a").removeClass("clicked").addClass("clicked").end().parents("li.closed").each( function () { _this.open_branch(this, true); });

			// SCROLL SELECTED NODE INTO VIEW
			var off_t = this.selected.offset().top;
			var beg_t = this.container.offset().top;
			var end_t = beg_t + this.container.height();
			var h_cor = (this.container.get(0).scrollWidth > this.container.width()) ? 40 : 20;
			if(off_t + 5 < beg_t) this.container.scrollTop(this.container.scrollTop() - (beg_t - off_t + 5) );
			if(off_t + h_cor > end_t) this.container.scrollTop(this.container.scrollTop() + (off_t + h_cor - end_t) );

			this.set_cookie("selected");
			this.settings.callback.onchange.call(null, this.selected.get(0), _this);
		},
		deselect_branch : function (obj) {
			if(this.locked) return this.error("LOCKED");
			var _this = this;
			var obj = this.get_node(obj);
			obj.children("a").removeClass("clicked");
			if(this.settings.rules.multiple != false && this.selected_arr.length > 1) {
				this.selected_arr = [];
				this.container.find("a.clicked").filter(":first-child").parent().each(function () {
					_this.selected_arr.push(jQuery(this));
				});
				if(obj.get(0) == this.selected.get(0)) {
					this.selected = this.selected_arr[0];
					this.set_cookie("selected");
				}
			}
			else {
				if(this.settings.rules.multiple != false) this.selected_arr = [];
				this.selected = false;
				this.set_cookie("selected");
			}
			if(this.selected)	this.settings.callback.onchange.call(null, this.selected.get(0), _this);
			else				this.settings.callback.onchange.call(null, false, _this);
		},
		toggle_branch : function (obj) {
			if(this.locked) return this.error("LOCKED");
			var obj = this.get_node(obj);
			if(obj.hasClass("closed"))	return this.open_branch(obj);
			if(obj.hasClass("open"))	return this.close_branch(obj); 
		},
		open_branch : function (obj, disable_animation, callback) {
			if(this.locked) return this.error("LOCKED");
			var obj = this.get_node(obj);
			if(!obj.size()) return this.error("OPEN: NO SUCH NODE");
			if(obj.hasClass("leaf")) return this.error("OPEN: OPENING LEAF NODE");

			if(this.settings.data.async && obj.find("li").size() == 0) {
				var _this = this;
				obj.children("ul:eq(0)").remove().end().append("<ul><li class='last'><a style='background-image:url(" + _this.settings.ui.theme_path + "default/throbber.gif)' href='#'>" + (_this.settings.lang.loading || "Loading ...") + "</a></li></ul>");
				obj.removeClass("closed").addClass("open");
				if(this.settings.data.type == "xml_flat" || this.settings.data.type == "xml_nested") {
					var xsl = (this.settings.data.type == "xml_flat") ? "flat.xsl" : "nested.xsl";
					var str = (this.settings.data.url.indexOf("?") == -1) ? "?id=" + encodeURIComponent(obj.attr("id")) : "&id=" + encodeURIComponent(obj.attr("id"));
					obj.children("ul:eq(0)").getTransform(this.path + xsl, this.settings.data.url + str, { params : { theme_path : _this.theme }, meth : this.settings.data.method, repl : true, callback: function (str, json) { 
							if(str.length < 15) {
								obj.removeClass("closed").removeClass("open").addClass("leaf").children("ul").remove();
								if(callback) callback.call();
								return;
							}
							_this.open_branch.apply(_this, [obj]); 
							if(callback) callback.call();
						} 
					});
				}
				else {
					jQuery.ajax({
						type		: this.settings.data.method,
						url			: this.settings.data.url, 
						data		: this.settings.data.async_data(obj), 
						dataType	: "json",
						success		: function (data, textStatus) {
							if(!data || data.length == 0) {
								obj.removeClass("closed").removeClass("open").addClass("leaf").children("ul").remove();
								if(callback) callback.call();
								return;
							}
							var str = "";
							if(data.length) {
								for(var i = 0; i < data.length; i++) {
									str += _this.parseJSON(data[i]);
								}
							}
							else str = _this.parseJSON(data);
							obj.children("ul:eq(0)").replaceWith("<ul>" + str + "</ul>");
							obj.find("li:last-child").addClass("last").end().find("li:has(ul)").not(".open").addClass("closed");
							obj.find("li").not(".open").not(".closed").addClass("leaf");
							_this.open_branch.apply(_this, [obj]);
							if(callback) callback.call();
						}
					});
				}
				return true;
			}
			else {
				if(parseInt(this.settings.ui.animation) > 0 && !disable_animation && !(jQuery.browser.msie && jQuery.browser.version < 7) ) {
					obj.children("ul:eq(0)").css("display","none");
					obj.removeClass("closed").addClass("open");
					obj.children("ul:eq(0)").slideDown(parseInt(this.settings.ui.animation), function() {
						jQuery(this).css("display","");
						if(callback) callback.call();
					});
				} else {
					obj.removeClass("closed").addClass("open");
					if(callback) callback.call();
				}
				this.set_cookie("open");
				this.settings.callback.onopen.call(null, obj.get(0), this);
				return true;
			}
		},
		close_branch : function (obj, disable_animation) {
			if(this.locked) return this.error("LOCKED");
			var _this = this;
			var obj = this.get_node(obj);
			if(parseInt(this.settings.ui.animation) > 0 && !disable_animation && !(jQuery.browser.msie && jQuery.browser.version < 7) && obj.children("ul:eq(0)").size() == 1) {
				obj.children("ul:eq(0)").slideUp(parseInt(this.settings.ui.animation), function() {
					obj.removeClass("open").addClass("closed");
					_this.set_cookie("open");
					jQuery(this).css("display","");
				});
			} 
			else {
				obj.removeClass("open").addClass("closed");
				this.set_cookie("open");
			}
			if(this.selected && obj.children("ul:eq(0)").find("a.clicked").size() > 0) {
				obj.find("li:has(a.clicked)").each(function() {
					_this.deselect_branch(this);
				});
				if(obj.children("a.clicked").size() == 0) this.select_branch(obj, (this.settings.rules.multiple != false && this.selected_arr.length > 0) );
			}
			this.settings.callback.onclose.call(null, obj.get(0), this);
		},
		open_all : function (obj) {
			if(this.locked) return this.error("LOCKED");
			var _this = this;
			obj = obj ? jQuery(obj) : this.container;
			obj.find("li.closed").each( function () { var __this = this; _this.open_branch.apply(_this, [this, true, function() { _this.open_all.apply(_this, [__this]); } ]); });
		},
		close_all : function () {
			if(this.locked) return this.error("LOCKED");
			var _this = this;
			jQuery(this.container).find("li.open").each( function () { _this.close_branch(this, true); });
		},
		show_lang : function (i) { 
			if(this.locked) return this.error("LOCKED");
			if(this.settings.languages[i] == this.current_lang) return true;
			var st = false;
			var id = this.container.attr("id") ? "#" + this.container.attr("id") : ".tree";
			st = get_css(id + " ." + this.current_lang, this.sn);
			if(st !== false) st.style.display = "none";
			st = get_css(id + " ." + this.settings.languages[i], this.sn);
			if(st !== false) st.style.display = "block";
			this.current_lang = this.settings.languages[i];
			return true;
		},
		cycle_lang : function() {
			if(this.locked) return this.error("LOCKED");
			var i = jQuery.inArray(this.current_lang, this.settings.languages);
			i ++;
			if(i > this.settings.languages.length - 1) i = 0;
			this.show_lang(i);
		},
		create : function (type, obj, data, icon, id ) {
			if(this.locked) return this.error("LOCKED");
			// NOTHING SELECTED
			obj = obj ? this.get_node(obj) : this.selected;
			if(!obj || !obj.size()) return this.error("CREATE: NO NODE SELECTED");
			if(!this.check("creatable", obj)) return this.error("CREATE: CANNOT CREATE IN NODE");

			var t = type || this.get_type(obj) || "";
			if(this.settings.rules.use_inline && this.settings.rules.metadata) {
				jQuery.metadata.setType("attr", this.settings.rules.metadata);
				if(typeof obj.metadata()["valid_children"] != "undefined") {
					if(jQuery.inArray(t, obj.metadata()["valid_children"]) == -1) return this.error("CREATE: NODE NOT A VALID CHILD");
				}
				if(typeof obj.metadata()["max_children"] != "undefined") {
					if( (obj.children("ul:eq(0)").children("li").size() + 1) > obj.metadata().max_children) return this.error("CREATE: MAX_CHILDREN REACHED");
				}
				var ok = true;
				obj.parents("li").each(function(i) {
					if(jQuery(this).metadata().max_depth) {
						if( (i + 1) >= jQuery(this).metadata().max_depth) {
							ok = false;
						}
					}
				});
				if(!ok) return this.error("CREATE: MAX_DEPTH REACHED");
			}
			if(obj.hasClass("closed")) {
				var _this = this;
				return this.open_branch(obj, true, function () { _this.create.apply(_this, [type, obj, data, icon, id]); } );
			}

			if(id)	$li = jQuery("<li id='" + id + "' />");
			else	$li = jQuery("<li />");
			// NEW NODE IS OF PASSED TYPE OR PARENT'S TYPE
			if(this.settings.rules.metadata) {
				jQuery.metadata.setType("attr", this.settings.rules.metadata);
				$li.attr(this.settings.rules.metadata, "type: '" + t + "'");
			}
			else {
				$li.attr(this.settings.rules.type_attr, t)
			}

			var icn = "";
			if((typeof icon).toLowerCase() == "string") {
				icn = icon;
				icn = icn.indexOf("/") == -1 ? this.theme + icn : icn;
			}
			if(this.settings.languages.length) {
				for(i = 0; i < this.settings.languages.length; i++) {
					if((typeof data).toLowerCase() == "string") val = data;
					else if(data && data[i]) {
						val = data[i];
					}
					else if(this.settings.lang.new_node) {
						if((typeof this.settings.lang.new_node).toLowerCase() != "string" && this.settings.lang.new_node[i]) 
							val = this.settings.lang.new_node[i];
						else 
							val = this.settings.lang.new_node;
					}
					else {
						val = "New folder";
					}
					if((typeof icon).toLowerCase() != "string" && icon && icon[i]) {
						icn = icon[i];
						icn = icn.indexOf("/") == -1 ? this.theme + icn : icn;
					}
					$li.append("<a href='#'" + ( icn.length ? " style='background-image:url(\"" + icn + "\");' " : " ") + "class='" + this.settings.languages[i] + "'>" + val + "</a>");
				}
			}
			else { $li.append("<a href='#'" + ( icn.length ? " style='background-image:url(\"" + icn + "\");' " : " ") + ">" + (data || this.settings.lang.new_node || "New folder") + "</a>"); }
			$li.addClass("leaf");
			if(this.settings.rules.createat == "top" || obj.children("ul").size() == 0) {
				this.moved($li,obj.children("a:eq(0)"),"inside", true);
			}
			else {
				this.moved($li,obj.children("ul:eq(0)").children("li:last").children("a:eq(0)"),"after",true);
			}
			this.select_branch($li.children("a:eq(0)"));
			if(!data) this.rename();
			return $li;
		},
		rename : function () {
			if(this.locked) return this.error("LOCKED");
			if(this.selected) {
				var _this = this;
				if(!this.check("renameable", this.selected)) return this.error("RENAME: NODE NOT RENAMABLE");
				if(!this.settings.callback.beforerename.call(null,this.selected.get(0), _this.current_lang, _this)) return this.error("RENAME: STOPPED BY USER");
				var obj = this.selected;
				if(this.current_lang)	obj = obj.find("a." + this.current_lang).get(0);
				else					obj = obj.find("a:first").get(0);
				last_value = obj.innerHTML;
				_this.inp = jQuery("<input type='text' />");
				_this.inp
					.val(last_value)
					.bind("mousedown",		function (event) { event.stopPropagation(); })
					.bind("mouseup",		function (event) { event.stopPropagation(); })
					.bind("click",			function (event) { event.stopPropagation(); })
					.bind("keyup",			function (event) { 
							var key = event.keyCode || event.which;
							if(key == 27) { this.value = last_value; this.blur(); return }
							if(key == 13) { this.blur(); return }
						});
				_this.inp.blur(function(event) {
						if(this.value == "") this.value == last_value; 
						jQuery(obj).html( jQuery(obj).parent().find("input").eq(0).attr("value") ).get(0).style.display = ""; 
						jQuery(obj).prevAll("span").remove(); 
						if(this.value != last_value) _this.settings.callback.onrename.call(null, _this.get_node(obj).get(0), _this.current_lang, _this);
						_this.inp = false;
					});
				var spn = jQuery("<span />").addClass(obj.className).append(_this.inp);
				spn.attr("style", jQuery(obj).attr("style"));
				obj.style.display = "none";
				jQuery(obj).parent().prepend(spn);
				_this.inp.get(0).focus();
				_this.inp.get(0).select();
			}
			else return this.error("RENAME: NO NODE SELECTED");
		},
		// REMOVE NODES
		remove : function(obj) {
			if(this.locked) return this.error("LOCKED");
			if(obj) {
				obj = this.get_node(obj);
				if(obj.size()) {
					if(!this.check("deletable", obj)) return this.error("DELETE: NODE NOT DELETABLE");
					if(!this.settings.callback.beforedelete.call(null,obj.get(0), _this)) return this.error("DELETE: STOPPED BY USER");
					$parent = obj.parent();
					obj = obj.remove();
					$parent.children("li:last").addClass("last");
					if($parent.children("li").size() == 0) {
						$li = $parent.parents("li:eq(0)");
						$li.removeClass("open").removeClass("closed").addClass("leaf").children("ul").remove();
						this.set_cookie("open");
					}
					this.settings.callback.ondelete.call(null, obj, this);
				}
			}
			else if(this.selected) {
				if(!this.check("deletable", this.selected)) return this.error("DELETE: NODE NOT DELETABLE");
				if(!this.settings.callback.beforedelete.call(null,this.selected.get(0), _this)) return this.error("DELETE: STOPPED BY USER");
				$parent = this.selected.parent();
				var obj = this.selected;
				if(this.settings.rules.multiple == false || this.selected_arr.length == 1) {
					var stop = true;
					var tmp = (this.selected.prev("li:eq(0)").size()) ? this.selected.prev("li:eq(0)") : this.selected.parents("li:eq(0)");
					// this.get_prev(true);
				}
				obj = obj.remove();
				$parent.children("li:last").addClass("last");
				if($parent.children("li").size() == 0) {
					$li = $parent.parents("li:eq(0)");
					$li.removeClass("open").removeClass("closed").addClass("leaf").children("ul").remove();
					this.set_cookie("open");
				}
				//this.selected = false;
				this.settings.callback.ondelete.call(null, obj, this);
				if(stop && tmp) this.select_branch(tmp);
				if(this.settings.rules.multiple != false && !stop) {
					var _this = this;
					this.selected_arr = [];
					this.container.find("a.clicked").filter(":first-child").parent().each(function () {
						_this.selected_arr.push(jQuery(this));
					});
					if(this.selected_arr.length > 0) {
						this.selected = this.selected_arr[0];
						this.remove();
					}
				}
			}
			else return this.error("DELETE: NO NODE SELECTED");
		},
		// FOR EXPLORER-LIKE KEYBOARD SHORTCUTS
		get_next : function(force) {
			var obj = this.hovered || this.selected;
			if(obj) {
				if(obj.hasClass("open"))						return force ? this.select_branch(obj.find("li:eq(0)")) : this.hover_branch(obj.find("li:eq(0)"));
				else if(jQuery(obj).nextAll("li").size() > 0)	return force ? this.select_branch(obj.nextAll("li:eq(0)")) : this.hover_branch(obj.nextAll("li:eq(0)"));
				else											return force ? this.select_branch(obj.parents("li").next("li").eq(0)) : this.hover_branch(obj.parents("li").next("li").eq(0));
			}
		},
		get_prev : function(force) {
			var obj = this.hovered || this.selected;
			if(obj) {
				if(obj.prev("li").size()) {
					var obj = obj.prev("li").eq(0);
					while(obj.hasClass("open")) obj = obj.children("ul:eq(0)").children("li:last");
					return force ? this.select_branch(obj) : this.hover_branch(obj);
				}
				else { return force ? this.select_branch(obj.parents("li:eq(0)")) : this.hover_branch(obj.parents("li:eq(0)")); }
			}
		},
		get_left : function(force, rtl) {
			if(this.settings.ui.rtl && !rtl) return this.get_right(force, true);
			var obj = this.hovered || this.selected;
			if(obj) {
				if(obj.hasClass("open"))	this.close_branch(obj);
				else {
					return force ? this.select_branch(obj.parents("li:eq(0)")) : this.hover_branch(obj.parents("li:eq(0)"));
				}
			}
		},
		get_right : function(force, rtl) {
			if(this.settings.ui.rtl && !rtl) return this.get_left(force, true);
			var obj = this.hovered || this.selected;
			if(obj) {
				if(obj.hasClass("closed"))	this.open_branch(obj);
				else {
					return force ? this.select_branch(obj.find("li:eq(0)")) : this.hover_branch(obj.find("li:eq(0)"));
				}
			}
		},
		toggleDots : function () {
			this.container.toggleClass("no_dots");
		},
		set_cookie : function (type) {
			if(this.settings.cookies === false) return false;
			switch(type) {
				/*case "selected":
					if(this.settings.rules.multiple != false && this.selected_arr.length > 1) {
						var val = Array();
						jQuery.each(this.selected_arr, function () {
							val.push(this.attr("id"));
						});
						val = val.join(",");
					}
					else var val = this.selected ? this.selected.attr("id") : false;
					jQuery.cookie(this.settings.cookies.prefix + '_selected',val,this.settings.cookies.opts);
					break;*/
				case "open":
					var str = "";
					this.container.find("li.open").each(function (i) { str += this.id + ","; });
					jQuery.cookie(this.settings.cookies.prefix + '_open',str.replace(/,$/ig,""),this.settings.cookies.opts);
					break;
			}
		},
		moved : function (what, where, how, is_new, is_copy) {
			var what	= jQuery(what);
			var $parent	= jQuery(what).parents("ul:eq(0)");
			var $where	= jQuery(where);
			// IF MULTIPLE
			if(what.size() > 1) {
				var _this = this;
				var tmp = this.moved(what.eq(0),where,how, false, is_copy);
				what.each(function (i) {
					if(i == 0) return;
					tmp = _this.moved(this, tmp.children("a:eq(0)"), "after", false, is_copy);
				})
				return;
			}
			if(is_copy) {
				what = what.clone();
				what.each(function (i) {
					this.id = this.id + "_copy";
					jQuery(this).find("li").each(function () {
						this.id = this.id + "_copy";
					})
					jQuery(this).find("a.clicked").removeClass("clicked");
				});
			}
			if(is_new) {
				if(!this.settings.callback.beforecreate.call(null,this.get_node(what).get(0), this.get_node(where).get(0),how,this)) return;
			}
			else {
				if(!this.settings.callback.beforemove.call(null,this.get_node(what).get(0), this.get_node(where).get(0),how,this)) return;
			}
			
			if(!is_new) {
				var tmp = jQuery(what).parents(".tree:eq(0)");
				// if different trees
				if(tmp.get(0) != this.container.get(0)) {
					tmp = tree_component.inst[tmp.attr("id")];
					// if there are languages - otherwise - no cleanup needed
					if(tmp.settings.languages.length) {
						var res = [];
						// if new tree has no languages - use current visible
						if(this.settings.languages.length == 0) res.push("." + tmp.current_lang);
						else {
							for(i in this.settings.languages) {
								for(j in tmp.settings.languages) {
									if(this.settings.languages[i] == tmp.settings.languages[j]) res.push("." + this.settings.languages[i]);
								}
							}
						}
						if(res.length == 0) return this.error("MOVE: NO COMMON LANGUAGES");
						what.find("a").removeClass("clicked").not(res.join(",")).remove();
					}
				}
			}

			// ADD NODE TO NEW PLACE
			switch(how) {
				case "before":
					$where.parents("ul:eq(0)").children("li.last").removeClass("last");
					$where.parents("li:eq(0)").before(what.removeClass("last"));
					$where.parents("ul:eq(0)").children("li:last").addClass("last");
					break;
				case "after":
					$where.parents("ul:eq(0)").children("li.last").removeClass("last");
					$where.parents("li:eq(0)").after(what.removeClass("last"));
					$where.parents("ul:eq(0)").children("li:last").addClass("last");
					break;
				case "inside":
					if(this.settings.data.async) {
						var obj = this.get_node($where);
						if(obj.hasClass("closed")) {
							var _this = this;
							return this.open_branch(obj, true, function () { _this.moved.apply(_this, [what, where, how, is_new, is_copy]); })
						}
					}
					if($where.parents("li:eq(0)").children("ul:first").size()) {
						if(this.settings.rules.createat == "top")	$where.parents("li:eq(0)").children("ul:first").prepend(what.removeClass("last")).children("li:last").addClass("last");
						else										$where.parents("li:eq(0)").children("ul:first").children(".last").removeClass("last").end().append(what.removeClass("last")).children("li:last").addClass("last");
					}
					else {
						what.addClass("last");
						$where.parents("li:eq(0)").append("<ul/>").removeClass("leaf").addClass("closed");
						$where.parents("li:eq(0)").children("ul:first").prepend(what);
					}
					if(!this.settings.data.async) {
						this.open_branch($where);
					}
					break;
				default:
					break;
			}
			// CLEANUP OLD PARENT
			if($parent.find("li").size() == 0) {
				var $li = $parent.parent();
				$li.removeClass("open").removeClass("closed").addClass("leaf").children("ul").remove();
				$li.parents("ul:eq(0)").children("li.last").removeClass("last").end().children("li:last").addClass("last");
				this.set_cookie("open");
			}
			else {
				$parent.children("li.last").removeClass("last");
				$parent.children("li:last").addClass("last");
			}
			if(is_new && how != "inside") where = this.get_node(where).parents("li:eq(0)");
			if(is_copy)		this.settings.callback.oncopy.call(null, this.get_node(what).get(0), this.get_node(where).get(0), how, this)
			else if(is_new)	this.settings.callback.oncreate.call(null, this.get_node(what).get(0), this.get_node(where).get(0), this.settings.insertAt, this);
			else			this.settings.callback.onmove.call(null, this.get_node(what).get(0), this.get_node(where).get(0), how, this);
			return what;
		},
		error : function (code) {
			this.settings.callback.error.call(null,code,this);
			return false;
		},
		lock : function (state) {
			this.locked = state;
			if(this.locked)	this.container.addClass("locked");
			else			this.container.removeClass("locked");
		},
		cut : function () {
			if(this.locked) return this.error("LOCKED");
			if(!this.selected) return this.error("CUT: NO NODE SELECTED");
			this.copy_nodes = false;
			this.cut_nodes = this.container.find("a.clicked").filter(":first-child").parent();
		},
		copy : function () {
			if(this.locked) return this.error("LOCKED");
			if(!this.selected) return this.error("COPY: NO NODE SELECTED");
			this.copy_nodes = this.container.find("a.clicked").filter(":first-child").parent();
			this.cut_nodes = false;
		},
		paste : function () {
			if(this.locked) return this.error("LOCKED");
			if(!this.selected) return this.error("PASTE: NO NODE SELECTED");
			if(!this.copy_nodes && !this.cut_nodes) return this.error("PASTE: NOTHING TO DO");
			if(this.copy_nodes && this.copy_nodes.size()) {
				if(!this.checkMove(this.copy_nodes, this.selected.children("a:eq(0)"), "inside")) return false;
				this.moved(this.copy_nodes, this.selected.children("a:eq(0)"), "inside", false, true);
				this.copy_nodes = false;
			}
			if(this.cut_nodes && this.cut_nodes.size()) {
				if(!this.checkMove(this.cut_nodes, this.selected.children("a:eq(0)"), "inside")) return false;
				this.moved(this.cut_nodes, this.selected.children("a:eq(0)"), "inside");
				this.cut_nodes = false;
			}
		},
		search : function(str) {
			var _this = this;
			if(!str || (this.srch && str != this.srch) ) {
				this.srch = "";
				this.srch_opn = false;
				this.container.find("a.search").removeClass("search");
			}
			this.srch = str;
			if(!str) return;
			if(this.settings.data.async) {
				if(!this.srch_opn) {
					var dd = jQuery.extend( { "search" : str } , this.settings.data.async_data(false) );
					jQuery.ajax({
						type		: this.settings.data.method,
						url			: this.settings.data.url, 
						data		: dd, 
						dataType	: "text",
						success		: function (data) {
							_this.srch_opn = jQuery.unique(data.split(","));
							_this.search.apply(_this,[str]);
						} 
					});
				}
				else if(this.srch_opn.length) {
					if(this.srch_opn && this.srch_opn.length) {
						var opn = false;
						for(var j = 0; j < this.srch_opn.length; j++) {
							if(this.get_node("#" + this.srch_opn[j]).size() > 0) {
								opn = true;
								var tmp = "#" + this.srch_opn[j];
								delete this.srch_opn[j];
								this.open_branch(tmp, true, function () { _this.search.apply(_this,[str]); } );
							}
						}
						if(!opn) {
							this.srch_opn = [];
							 _this.search.apply(_this,[str]);
						}
					}
				}
				else {
					var selector = "a";
					// IF LANGUAGE VERSIONS
					if(this.settings.languages.length) selector += "." + this.current_lang;
					this.container.find(selector + ":contains('" + str + "')").addClass("search");
					this.srch_opn = false;
				}
			}
			else {
				var selector = "a";
				// IF LANGUAGE VERSIONS
				if(this.settings.languages.length) selector += "." + this.current_lang;
				this.container.find(selector + ":contains('" + str + "')").addClass("search").parents("li.closed").each( function () { _this.open_branch(this, true); });
			}
		},

		destroy : function() {
			try {
				var evts = ["click","dblclick","contextmenu","mouseover","mousedown"];
				for(i in evts) {
					var idxer = this.container.indexer(evts[i]);
					idxer.stop();
					jQuery.removeData( idxer.listener, idxer.event + '.indexer' );
				}
			} catch(err) { }
			this.container.unbind();

			this.container.removeClass("tree").children("ul").removeClass("tree-" + this.settings.ui.theme_name).find("li").removeClass("leaf").removeClass("open").removeClass("closed").removeClass("last").children("a").removeClass("clicked");

			if(this.cntr == tree_component.focused) {
				for(i in tree_component.inst) {
					if(i != this.cntr && i != this.container.attr("id")) {
						tree_component.inst[i].focus();
						break;
					}
				}
			}
			delete tree_component.inst[this.cntr];
			delete tree_component.inst[this.container.attr("id")];
			tree_component.cntr --;
		}
	}
};
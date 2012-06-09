(function($) {
	// Expose globally to allow widgets to use the same jQuery object
	// in order to share the same `data` objects containing id and name.
	// This fix the issue arising when another jQuery version is loaded between
	// this script and the plugin_editor mechanism in the `PlaceholderPluginEditorWidget`
	// see 'templates/admin/cms/page/widgets/plugin_editor.html'
	cms_plugin_editor_jQuery = $;
	$(document).ready(function() {
		// Add Plugin Handler
		$('span.add-plugin').click(function(){
		 var select = $(this).parent().children("select[name=plugins]");
			var pluginvalue = select.attr('value');
			var placeholder_id = $(this).parent().parent().data('id');
			//var splits = window.location.href.split("/");

			var language = $('input.language_button.selected').attr('name');

			if (!language) {
				language = $('input[name=language]').attr("value");
			}
			// The new placeholder branch allows adding non-language plugins!
			if (!language) {
				//alert("Unable to determine the correct language for this plugin! Please report the bug!");
			}

			var target_div = $(this).parent().parent().parent().children('div.plugin-editor');
			if (pluginvalue) {
				var pluginname = select.children('[selected]').text();
				var ul_list = $(this).parent().parent().children("ul.plugin-list");
				$.ajax({
					url: "add-plugin/", dataType: "html", type: "POST",
					data: ({ placeholder:placeholder_id, plugin_type:pluginvalue, language:language }),
					success: function(data) {
						loadPluginForm(target_div, data);
						ul_list.append('<li id="plugin_' + data + '" class="' + pluginvalue + ' active"><span class="drag"></span><span class="text">' + pluginname + '</span><span class="delete"></span></li>');
						setclickfunctions();
					},
					error: function(xhr) {
						if (xhr.status < 500) {
							alert(xhr.responseText);
						}
					}
				});
			}
		});

		// Copy Plugins Handler
		$('span.copy-plugins').click(function(){
			var copy_from_language = $(this).parent().children("select[name=copy-plugins]").attr("value");
			var placeholder = $(this).parent().parent().data('id');
			var splits = window.location.href.split("/");
			var page_id = splits[splits.length-2];

			var to_language = $('input.language_button.selected').attr('name');

			if (!to_language) {
				to_language = $('input[name=language]').attr("value");
			}

			if (!to_language) {
				//alert("Unable to determine the correct language for this plugin! Please report the bug!");
			}

			//var target_div = $(this).parent().parent().parent().children('div.plugin-editor');
			if ((copy_from_language) && (copy_from_language != "")) {
			 var ul_list = $(this).parent().parent().children("ul.plugin-list");
				$.ajax({
					url: "copy-plugins/", dataType: "html", type: "POST",
					data: { page_id: page_id, placeholder: placeholder, copy_from: copy_from_language, language: to_language },
					success: function(data) {
						ul_list.append(data);
						setclickfunctions();
					},
					error: function(xhr) {
						if (xhr.status < 500) {
							alert(xhr.responseText);
						}
					}
				});
			}
		});

		// Drag'n'Drop sorting/moving
		$('ul.plugin-list').sortable({
			handle:'span.drag',
			axis:'y',
			opacity:0.9,
			zIndex:2000,
			dropOnEmpty:true,
			connectWith: '.plugin-list',

			update:function(event, ui){
				var array = $(this).sortable('toArray');
				var d = "";
				for(var i=0;i<array.length;i++){
					d += array[i].split("plugin_")[1];
					if (i!=array.length-1){
						d += "_";
					}
				}
				if (ui.sender) {
					// moved to new placeholder
					var plugin_id = ui.item.attr('id').split('plugin_')[1];
					var slot_name = ui.item.parent().parent().data('name');
					var placeholder_id = ui.item.parent().parent().data('id');
					$.post("move-plugin/", {
						placeholder: slot_name,
						placeholder_id: placeholder_id,
						plugin_id: plugin_id,
						ids: d
					}, function(){}, "json");
				} else {
					// moved in placeholder
					if (d) {
						$.post("move-plugin/", { ids:d }, function(){}, "json");
					}
				}

			}
		});

		setclickfunctions();
	});

	function plugin_select_click_handler(){
		var target = $(this).parent().parent().parent().parent().children("div.plugin-editor");
		var id = $(this).parent().attr("id").split("plugin_")[1];
		loadPluginForm(target, id);
		return false;
	}

	function plugin_delete_click_handler(){
		var plugin_id = $(this).parent().attr("id").split("plugin_")[1];
		var question = gettext("Are you sure you want to delete this plugin?");
		var answer = confirm(question, true);
		var pagesplits = window.location.href.split("/");
		var page_id = pagesplits[pagesplits.length-2];
		if(answer){
			$.post("remove-plugin/", { plugin_id:plugin_id, page_id:page_id }, function(data){
				var splits = data.split(",");
				id = splits.shift();
				$("#plugin_"+id).remove();
				$("#iframe_"+id).parent().html("<p>" + splits.join(",") + "</p>")
			}, "html");
		}
	}

	function setclickfunctions(){
		$('ul.plugin-list .text').unbind('click', plugin_select_click_handler);
		$('ul.plugin-list span.delete').unbind('click', plugin_delete_click_handler);

		$('ul.plugin-list .text').click(plugin_select_click_handler);
		$('ul.plugin-list span.delete').click(plugin_delete_click_handler);
	}

	// TODO: depreciated? not used anywhere
	/*function load_plugin(li){
		var target = li.parent().parent().parent().children("div.plugin-editor");
		var id = li.attr("id").split("plugin_")[1];
		loadPluginForm(target, id);
	}*/

	function loadPluginForm(target, id){
		var object = '<iframe id="iframe_'+id+'" src="edit-plugin/'+id+'/" frameborder="0"></iframe>';
		target.html(object);
		$('ul.plugin-list .active').removeClass("active");
		$('#plugin_'+id).addClass("active");
	}

// global functions
	setiframeheight = function(height, id){
		$('#iframe_'+id).height(height+"px");
	};

	hide_iframe = function (id, type, title, msg){
		html = "<strong>"+type+"</strong>";
		if( title != "" && title != null){
			html += " [ "+title+ " ]"
		}
		$('#plugin_'+id+" span.text").html(html);
		$('#iframe_'+id).parent().html("<p>"+msg+"</p>");
	};

	removed_cancelled_plugin = function(plugin_id) {
		$('#plugin_'+plugin_id).remove();
	}

})(jQuery);

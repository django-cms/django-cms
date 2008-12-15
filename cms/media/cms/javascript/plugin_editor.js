$(document).ready(function() {
	$('span.add-plugin').click(function(){
		var select = $(this).parent().children("select")
		var pluginvalue = select.attr('value')
		var placeholder = $(this).parent().parent().parent().parent().parent().children("h2").text()
		var page_id = window.location.href.split("/")[6]  
		var language = $('#id_language').attr('value')
		var target_div = $(this).parent().parent().parent().children('div.plugin-editor')
		if (pluginvalue) {
			var pluginname = select.children('[@selected]').text()
			var ul_list = $(this).parent().parent().children("ul.plugin-list")
			$.post("add-plugin/", { page_id:page_id, placeholder:placeholder, plugin_type:pluginvalue, language:language }, function(data){
				loadPluginForm(target_div, data)
				ul_list.append('<li id="plugin_'+data+'" class="' + pluginvalue + ' active"><span class="drag"></span><span class="text">' + pluginname + '</span><span class="delete"></span></li>')
				setclickfunctions();
			}, "html" );
		}
	});
	setclickfunctions();
});

function setclickfunctions(){
	$('ul.plugin-list .text').click(function(){
		var target = $(this).parent().parent().parent().parent().children("div.plugin-editor")
		var id = $(this).parent().attr("id").split("plugin_")[1]
		loadPluginForm(target, id)
		return false
	})
	
	$('ul.plugin-list .delete').click(function(){
		var plugin_id = $(this).parent().attr("id").split("plugin_")[1]
		$.post("remove-plugin/", { plugin_id:plugin_id }, function(data){
			$("#plugin_"+data).remove()
		}, "html");
   	});
   
   	$('ul.plugin-list .drag').click(function(){
    	alert("drag");
   	});
}

function setiframeheight(){
	alert("setiframeheight");
}

function loadPluginForm(target, id){
	var object = '<iframe src="/admin/cms/page/edit-plugin/'+id+'"></iframe>' 
	target.html(object)
	$('ul.plugin-list .active').removeClass("active")
	$('#plugin_'+id).addClass("active")
};
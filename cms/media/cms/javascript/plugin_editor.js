$(document).ready(function() {
	$('span.add-plugin').click(function(){
		var select = $(this).parent().children("select")
		var pluginvalue = select.attr('value')
		var placeholder = $(this).parent().parent().parent().children("h2").text()
		var page_id = window.location.href.split("/")[6]  
		var language = $('#id_language').attr('value')
		var target_div = $(this).parent().parent().parent().children('div.plugin-editor')
		console.log(page_id)
		
		if (pluginvalue) {
			var pluginname = select.children('[@selected]').text()
			var ul_list = $(this).parent().parent().children("ul.plugin-list")
			$.post("add-plugin/", { page_id:page_id, placeholder:placeholder, plugin_type:pluginvalue, language:language }, function(data){
				loadPluginForm(target_div, data)
				ul_list.append('<li id="plugin_'+data+'" class="' + pluginvalue + '"><a href="#"><span class="drag"></span><span class="text">' + pluginname + '</span><span class="delete"></span></a></li>')
			}, "html" );
		
		}
	});
	$('ul.plugin-list a .text').click(function(){
		var target = $(this).parent().parent().parent().parent().parent().children("div.plugin-editor")
		var id = $(this).parent().parent().attr("id").split("plugin_")[1]
		loadPluginForm(target, id)
		return false
	})
});


function loadPluginForm(target, id){
	console.log(id)
	var object = '<object id="page" type="text/html" data="/admin/cms/page/edit-plugin/'+id+'"></object>' 
	target.html(object)
	$('li#plugin_'+id).addClass("active")
	console.log('#plugin_'+id)
	console.log($('#plugin_'+id))
};
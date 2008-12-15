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
			$(this).parent().parent().children("ul.plugin-list").append("<li class=" + pluginvalue + "><a href='#'><span class='drag'></span><span class='text'>" + pluginname + "</span><span class='delete'>delete</span></a></li>")
			$.post("add-plugin/", { page_id:page_id, placeholder:placeholder, plugin_type:pluginvalue, language:language }, function(data){
				target_div.html(data)
				target_div.children("form").submit(function() {
					alert("send")
					return false;
				});

			}, "html" );
		
		}
	});
});


function loadPluginForm(name){
	
}
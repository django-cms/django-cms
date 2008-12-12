$(document).ready(function() {
    $('#id_template').change(function() {
        var index = this.selectedIndex;
        var array = window.location.href.split('?');
        var query = $.query.set('template', this.options[index].value).toString();
        window.location.href=array[0]+query;
    });
    $('#id_language').change(function() {
        var index = this.selectedIndex;
        var array = window.location.href.split('?');
        var query = $.query.set('language', this.options[index].value).toString();
        window.location.href=array[0]+query;
    });
    document.getElementById("id_title").focus();
    var template = $.query.get('template');
    if(template) {
        $('#id_template').find("option").each(function() {
            this.selected = false;
            if (template==this.value)
                this.selected = true;
        })
    }
    $("#id_slug").change(function() { this._changed = true; });
    $("#id_title").keyup(function() {
        var e = $("#id_slug")[0];
        if (!e._changed) {
            e.value = URLify(this.value, 64);
        }
    });
    $('span.add-plugin').click(function(){
		var select = $(this).parent().children("select")
		var pluginvalue = select.attr('value')
		if (pluginvalue) {
			var pluginname = select.children('[@selected]').text()
			$(this).parent().children("ul.plugin-list").append("<li class=" + pluginvalue + ">" + pluginname + "</li>")
		}
	});
});
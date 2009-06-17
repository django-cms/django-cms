$(document).ready(function() {
        var new_slug = true
        if($('#id_slug')[0].value){
            new_slug = false
        }
	$.each(["language", "template"], function(i, label){
        var select = $('select#id_'+label);
        select.change(function() {
			changed = false;
			if($("#id_slug")[0]._changed){
				changed = true;
			}
			if($("#id_title")[0]._changed){
				changed = true;
			}
			if($("#id_status")[0]._changed){
				changed = true;
			}
			if($('iframe').length){
				changed = true;
			}
            var array = window.location.href.split('?');
            var query = $.query.set(label, this.options[this.selectedIndex].value).toString();
            if (changed) {
				var question = gettext("Are you sure you want to change the %(field_name)s without saving the page first?")
				var answer = confirm(interpolate(question, {
					field_name: select.prev().text().slice(0, -1),
				}, true));
			}else{
				var answer = true;
			}
            if (answer) {
                window.location.href = array[0]+query;
            } else {
                this.selectedIndex = index;
            }
        
        });
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
	$('#id_title').change(function() {this._changed = true; })
	$('#id_status').change(function() {this._changed = true; })
    $("#id_title").keyup(function() {
        var e = $("#id_slug")[0];
        if (!e._changed && new_slug) {
            e.value = URLify(this.value, 64);
        }
    });
	$('#page_form').submit(function(){            
		if($('iframe').length){
			var question = gettext("Not all plugins are saved. Are you sure you want to save the page? All unsaved plugin content will be lost.")
			var answer = confirm(question, true);
			return answer
		}
	})
	$('ul.plugin-list').each(function(i, a){
		var lis = $(this).children("li")
		if (lis.length == 1){
			load_plugin($($(this).children("li")[0]));
		}
    });
    
});


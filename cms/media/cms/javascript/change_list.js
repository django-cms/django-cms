/*
jQuery.cookie = function(name, value, options) {
    if (typeof value != 'undefined') { // name and value given, set cookie
        options = options || {};
        if (value === null) {
            value = '';
            options.expires = -1;
        }
        var expires = '';
        if (options.expires && (typeof options.expires == 'number' || options.expires.toUTCString)) {
            var date;
            if (typeof options.expires == 'number') {
                date = new Date();
                date.setTime(date.getTime() + (options.expires * 24 * 60 * 60 * 1000));
            } else {
                date = options.expires;
            }
            expires = '; expires=' + date.toUTCString(); // use expires attribute, max-age is not supported by IE
        }
        // CAUTION: Needed to parenthesize options.path and options.domain
        // in the following expressions, otherwise they evaluate to undefined
        // in the packed version for some reason...
        var path = options.path ? '; path=' + (options.path) : '';
        var domain = options.domain ? '; domain=' + (options.domain) : '';
        var secure = options.secure ? '; secure' : '';
        document.cookie = [name, '=', encodeURIComponent(value), expires, path, domain, secure].join('');
    } else { // only name given, get cookie
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
};

*/
$(document).ready(function() {
	var tree = new tree_component();
	tree.init($("div.tree"), {
			rules:{
		        clickable   : "all",
		        renameable  : "none",
		        deletable   : "all",
		        creatable   : "all",
		        draggable   : "all",
		        dragrules   : "all"
		    },
			path:false,
			ui:{
		        dots        : true,
		        rtl         : false,
		        animation   : 0,
		        hover_mode  : true,
		        theme_path  : false,
		        theme_name  : "default",
				a_class		: "title"
		    }
	   });
	
   
    var selected_page = false;
    var action = false;
    
    // let's start event delegation
	
    $('#changelist li').click(function(e) {
        // I want a link to check the class
        if(e.target.tagName == 'IMG' || e.target.tagName == 'SPAN')
            var target = e.target.parentNode;
        else
            var target = e.target;
        var jtarget = $(target);
        
        if(jtarget.hasClass("move")) {
			var id = e.target.id.split("move-link-")[1];
			if(id==null){
				id = e.target.parentNode.id.split("move-link-")[1];
			}
            var page_id = id
            selected_page = page_id;
            action = "move";
			$('span.move-target-container').show();
            $('#page_'+page_id).addClass("selected")
			$('#page_'+page_id+' span.move-target-container').hide();
            return false;
        }
        
        if(jtarget.hasClass("addlink")) {
			console.log("add")
            $("tr").removeClass("target");
            $("#changelist table").removeClass("table-selected");
            var page_id = target.id.split("add-link-")[1];
            selected_page = page_id;
            action = "add";
            $('tr').removeClass("selected");
            $('#page-row-'+page_id).addClass("selected");
            $('.move-target-container').hide();
            $('#move-target-'+page_id).show();
            return false;
        }
        
        if(jtarget.hasClass("publish-checkbox")) {
            var p = jtarget.attr("name").split("status-")[1];
            // if I don't put data in the post, django doesn't get it
            $.post("/admin/cms/page/"+p+"/change-status/", {1:1}, function(val) {
                var img = $('img', jtarget.parent())[0];
                if(val=="0") {
                    jtarget.attr("checked", "");
                    img.src = img.src.replace("-yes.gif", "-no.gif");
                } else {
                    jtarget.attr("checked", "checked");
                    img.src = img.src.replace("-no.gif", "-yes.gif");
                }
                jtarget.attr("value", val);
            });
			e.stopPropagation();
            return true;
        }
		
		if(jtarget.hasClass("navigation-checkbox")) {
            var p = jtarget.attr("name").split("navigation-")[1];
            // if I don't put data in the post, django doesn't get it
            $.post("/admin/cms/page/"+p+"/change-navigation/", {1:1}, function(val) {
                var img = $('img', jtarget.parent())[0];
                if(val=="0") {
                    jtarget.attr("checked", "");
                    img.src = img.src.replace("-yes.gif", "-no.gif");
                } else {
                    jtarget.attr("checked", "checked");
                    img.src = img.src.replace("-no.gif", "-yes.gif");
                }
                jtarget.attr("value", val);
            });
            return true;
        }
        
        if(jtarget.hasClass("move-target")) {
			console.log("move target")
            if(jtarget.hasClass("left"))
                var position = "left";
            if(jtarget.hasClass("right"))
                var position = "right";
            if(jtarget.hasClass("first-child"))
                var position = "first-child";
            var target_id = target.parentNode.id.split("move-target-")[1];
			console.log(target_id)
            if(action=="move") {
                $.post("/admin/cms/page/"+selected_page+"/move-page/", {
                        position:position,
                        target:target_id
                    },
                    function(html) {
						console.log(html)
						if(html=="ok"){
							console.log(tree)
							
							console.log(selected_page)
							console.log(target_id)
							console.log(position)
							var tree_pos = false;
							if (position == "left"){
								tree_pos = "before"
							}else if(position == "right"){
								tree_pos = "after"
							}else{
								tree_pos = "inside"
							}
							tree.moved("#page_"+selected_page,$("#page_"+target_id+" a.title")[0], tree_pos, false, false)
						}else{
							
						}
                        
                        $('#page-row-'+selected_page).addClass("selected");
                        var msg = $('<span>Successfully moved</span>');
                        $($('#page-row-'+selected_page+" td")[0]).append(msg);
                        msg.fadeOut(5000);
                    }
                );
                $('.move-target-container').hide();
            }
            if(action=="add") {
                var query = $.query.set('target', target_id).set('position', position).toString();
                window.location.href += 'add/'+query;
            }
            //selected_page = false;
            return false;
        }
        
        /*if(jtarget.hasClass("collapse")) {
            var the_id = jtarget.attr('id').substring(1);
            jtarget.toggleClass('collapsed');
            if(jtarget.hasClass('collapsed')) {
                hide_children(the_id);
            } else {
                show_children(the_id);
            }
            save_collapsed();
            return false;
        };*/
        
        return true;
    });
	
	/*
	$.fn.syncWidth = function(max) {
		$(this).each(function() {
			var val= $(this).width();
			if(val > max){max = val;}	
		});
 		$(this).each(function() {
  			$(this).css("width",max+'px');
		});
		return this;
	};	
	
	$('#sitemap .col-actions').syncWidth(80);
	$('#sitemap .col-published').syncWidth(0);
	$('#sitemap .col-navigation').syncWidth(0);
	$('#sitemap .col-softroot').syncWidth(0);
	$('#sitemap .col-template').syncWidth(0);
	$('#sitemap .col-creator').syncWidth(0);*/
});

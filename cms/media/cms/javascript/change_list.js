var tree

function initTree(){
	tree = new tree_component();
	tree.init($("div.tree"), {
		rules: {
			clickable: "all",
			renameable: "none",
			deletable: "all",
			creatable: "all",
			draggable: "all",
			dragrules: "all"
		},
		path: false,
		ui: {
			dots: true,
			rtl: false,
			animation: 0,
			hover_mode: true,
			theme_path: false,
			theme_name: "default",
			a_class: "title"
		},
		cookies : {},
		callback: {
			onmove: function(what, where, position, tree){
				item_id = what.id.split("page_")[1];
				target_id = where.id.split("page_")[1];
				if (position == "before") {
					position = "left"
				}
				else 
					if (position == "after") {
						position = "right"
					}
					else {
						position = "first-child"
					}
				moveTreeItem(item_id, target_id, position, false)
			},
			onchange: function(node, tree){
				self.location = node.id.split("page_")[1]
			}
		}
	});
};

$(document).ready(function() { 
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
			$('span.move-target-container, span.line, a.move-target').show();
            $('#page_'+page_id).addClass("selected")
			$('#page_'+page_id+' span.move-target-container').hide();
			e.stopPropagation();
            return false;
        }
        
        if(jtarget.hasClass("copy")) {
			var id = e.target.id.split("copy-link-")[1];
			if(id==null){
				id = e.target.parentNode.id.split("copy-link-")[1];
			}
			selected_page = id;
            action = mark_copy_node(id)
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
            $("tr").removeClass("target");
            $("#changelist table").removeClass("table-selected");
            var page_id = target.id.split("add-link-")[1];
            selected_page = page_id;
            action = "add";
            $('tr').removeClass("selected");
            $('#page-row-'+page_id).addClass("selected");
            $('.move-target-container').hide();
            $('a.move-target, span.line, #move-target-'+page_id).show();
			e.stopPropagation();
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
			e.stopPropagation();
            return true;
        }
        
        if(jtarget.hasClass("move-target")) {
            if(jtarget.hasClass("left"))
                var position = "left";
            if(jtarget.hasClass("right"))
                var position = "right";
            if(jtarget.hasClass("first-child"))
                var position = "first-child";
            var target_id = target.parentNode.id.split("move-target-")[1];
            if(action=="move") {
				moveTreeItem(selected_page, target_id, position, tree)
                $('.move-target-container').hide();
            }else if(action=="copy") {
            	site = $('select#site-select')[0].value
				copyTreeItem(selected_page, target_id, position, tree, site)
                $('.move-target-container').hide();
            }else if(action=="add") {
                site = $('select#site-select')[0].value
                window.location.href = window.location.href.split("?")[0].split("#")[0] + 'add/?target='+target_id+"&position="+position+"&site="+site;
            }else{
            	console.log("no action defined!")
            }
			e.stopPropagation();
            return false;
        }
        return true;
    });
	/* Colums width sync */
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
	$("div#sitemap").show()
	$('#sitemap ul .col-actions').syncWidth(80);
	$('#sitemap ul .col-published').syncWidth(0);
	$('#sitemap ul .col-navigation').syncWidth(0);
	$('#sitemap ul .col-softroot').syncWidth(0);
	$('#sitemap ul .col-template').syncWidth(0);
	$('#sitemap ul .col-creator').syncWidth(0);	
	/* Site Selector */
	$('select#site-select').change(function(event){
		var id = this.value
		var url = window.location.href
		if(action=="copy"){
			url = insert_into_url(url, "copy", selected_page);
		}else{
			url = remove_from_url(url, "copy");
		}
		url = insert_into_url(url, "sites__id__exact", id)
		window.location = url;
	});
	var copy_splits = window.location.href.split("copy=")
	if(copy_splits.length > 1){
		var id = copy_splits[1].split("&")[0];
		selected_page = id;
		action = mark_copy_node(id);
		                                   
	}
	
	
});


function mark_copy_node(id){
    
	$('a.move-target, span.move-target-container, span.line').show();
    $('#page_'+id).addClass("selected")
	$('#page_'+id).parent().parent().children('div.cont').find('a.move-target.first-child, span.second').hide();
    $('#page_'+id).parent().parent().children('ul').children('li').children('div.cont').find('a.move-target.left, a.move-target.right, span.first, span.second').hide();
    return "copy"
}

function insert_into_url(url, name, value){
	dash_splits = url.split("#")
	url = dash_splits[0]
	var splits = url.split(name + "=");
	var get_args = false;
	if(url.split("?").length>1){
		get_args = true;
	}
	if(splits.length > 1){
		var after = ""
		if (splits[1].split("&").length > 1){
			after = splits[1].split("&")[1];
		}
		url = splits[0] + name + "=" + value + "&" + after;
	}else{
		if(get_args){
			url = url + "&" + name + "=" + value;
		}else{
			url = url + "?" + name + "=" + value;
		}
	}
	if(dash_splits.length>1){
		url += dash_splits[1]
	}
	return url
}

function remove_from_url(url, name){
	var splits = url.split(name + "=");
	if(splits.length > 1){
		var after = ""
		if (splits[1].split("&").length > 1){
			after = splits[1].split("&")[1];
		}
		if (splits[0].substr(splits[0].length-2, splits[0]-length-1)=="?"){
			url = splits[0] + after;
		}else{
			url = splits[0] + "&" + after;
		}
	}
	return url;
}


function moveTreeItem(item_id, target_id, position, tree){

	$.post("./"+item_id+"/move-page/", {
            position:position,
            target:target_id
        },
        function(html) {
			if(html=="ok"){
				if (tree) {
					var tree_pos = false;
					if (position == "left") {
						tree_pos = "before"
					}else if (position == "right") {
						tree_pos = "after"
					}else {
						tree_pos = "inside"
					}
					tree.moved("#page_" + item_id, $("#page_" + target_id + " a.title")[0], tree_pos, false, false)
				}else{
					moveSuccess($('#page_'+item_id + " div.col1:eq(0)"))
				}
			}else{
				moveError($('#page_'+item_id + " div.col1:eq(0)"))   
			}
        }
    );
};


function copyTreeItem(item_id, target_id, position, tree, site){

	$.post("./"+item_id+"/copy-page/", {
            position:position,
            target:target_id,
            site:site
        },
        function(html) {
			if(html=="ok"){
				window.location=window.location.href
			}else{
				moveError($('#page_'+item_id + " div.col1:eq(0)"))   
			}
        }
    );
};
var tree;

function initTree(){
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
			use_inline: true,
			//droppable : ["tree_drop"]
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
				self.location = node.id.split("page_")[1];
			}
		}
	};
	
	if (!$($("div.tree").get(0)).hasClass('root_allow_children')){
		// disalow possibility for adding subnodes to main tree, user doesn't
		// have permissions for this
		options.rules.dragrules = ["node inside topnode", "node * node"];
	}
	
	//dragrules : [ "folder * folder", "folder inside root", "tree-drop * folder" ],
        
	
	//console.log($("div.tree").get(0).className);
	tree.init($("div.tree"), options);
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
			$('span.move-target-container').show();
            $('#page_'+page_id).addClass("selected")
			$('#page_'+page_id+' span.move-target-container').hide();
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
            var page_id = target.id.split("add-link-")[1];
            selected_page = page_id;
            action = "add";
            $('tr').removeClass("selected");
            $('#page-row-'+page_id).addClass("selected");
            $('.move-target-container').hide();
            $('#move-target-'+page_id).show();
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
        
		// moderation
		if(jtarget.hasClass("moderator-checkbox")) {
            var pageId = jtarget.parents('li[id^=page_]').attr('id').split('_')[1];
            parent = jtarget.parents('div.col-moderator');
			
			value = 0;
			parent.find('input[type=checkbox]').each(function(i, el){
				value += $(el).attr("checked") ? parseInt($(el).val()) : 0;
			})
			
			//parent.load("/admin/cms/page/" + pageId + "/change-moderation/", { moderate: value });
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
            }
            if(action=="add") {
                //var query = $.query.set('target', target_id).set('position', position).toString();
                site = $('select#site-select')[0].value
                window.location.href = window.location.href.split("?")[0] + 'add/?target='+target_id+"&position="+position+"&site="+site;
            }
            //selected_page = false;
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
	$('#sitemap ul .col-actions').syncWidth(0);
	$('#sitemap ul .col-published').syncWidth(0);
	$('#sitemap ul .col-navigation').syncWidth(0);
	$('#sitemap ul .col-softroot').syncWidth(0);
	$('#sitemap ul .col-template').syncWidth(0);
	$('#sitemap ul .col-creator').syncWidth(0);	
	/* Site Selector */
	$('select#site-select').change(function(event){
		var id = this.value
		var url = window.location.href
		var get_args = false;
		console.log(url)
		
		if(url.split("?").length>1){
			get_args = true;
			console.log("get args = true")
		}
		var splits = url.split("sites__id__exact=")
		if(splits.length > 1){
			window.location = splits[0] + "sites__id__exact=" + id + splits[1].substr(1,splits[1].length);
		}else{
			if(get_args){
				window.location = url + "&sites__id__exact=" + id
			}else{
				window.location = url + "?sites__id__exact=" + id
			}
		}
	});
	
	
});


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


$(function(){
	$('div.col-moderator input').checkBox({addLabel:false});
	
})

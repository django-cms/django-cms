/* javascript for the frontend editing toolbar */

jQuery.noConflict();

function hide_iframe(){
    // needs to be a global function because it gets called 
    // from the iframe as `parent.hide_iframe`
    jQuery.nyroModalRemove();
    jQuery("#nyroModalWrapper .wrapperIframe").html("");
    window.location = window.location.href;
}

jQuery(document).ready(function($) {

    jQuery.fn.swapWith = function(to) {
        return this.each(function() {
            var copy_to = $(to).clone(true);
            var copy_from = $(this).clone(true);
            $(to).replaceWith(copy_from);
            $(this).replaceWith(copy_to);
        });
    };
        

    var page_id = -1;
    var plugin_id = -1;
    var placeholder = "";
    var plugin_type = "";
    var bodyBackgroundPos;
    var bodyBackgroundPosXFull;
    var bodyBackgroundPosYFull;
    var bodyBackgroundPosY;
    var bodyBackgroundPosUnit;


    function move(direction){
        var result = new Array();
        var index = -1;
        var plugins = $("div.cms_plugin_holder[rel='" + placeholder+"']");
        var before = new Array();
        var after = new Array();
        for(var i=0; i<plugins.length; i++){
            var plugin = $(plugins[i]);
            var id = plugin.attr("id").split("cms_plugin_")[1].split("_")[1]
            if (id == plugin_id){
                index = i;
            }else{
                if(index == -1){
                    before.push(id);
                }else{
                    after.push(id);
                }
            }
        }
        if(direction == 1){
            if(after.length){
                result = result.concat(before, [after.shift(), plugin_id], after);
            }else{
                direction = 2;
                result = result.concat([plugin_id], before);
            }
        }
        if(direction == -1){
            if(before.length){
                var mover = before.pop();
                result = result.concat(before, [plugin_id, mover], after);
            }else{
                direction = -2;
                result = result.concat([plugin_id], after);
            }
        }


        $.post(urls.cms_page_move_plugin, { ids:result.join("_") }, function(data){
        
        });

        var current = $("#cms_plugin_"+page_id+"_"+plugin_id)
    
        if(direction == 1){
            current.swapWith(current.next());
        }else if(direction == -1){
            current.swapWith(current.prev());
        }else if(direction == 2){
            $(plugins[0]).before(current.clone());
            current.remove();
        }else if(direction == -2){
            $(plugins[plugins.length-1]).after(current.clone());
            current.remove();
        }
        $("#cms_plugin_overlay").hide();
        hideCMStoolbarSubmenus();
        $("#cms_plugin_"+page_id+"_"+plugin_id).makeoverlay("#cms_plugin_overlay2");
    }

    function edit_plugin(page_id, plugin_id){    
        $.nyroModalManual({
            zIndexStart: 80000,
            type: 'iframe',
            modal: false,
            forceType: 'iframe',
            url: urls.cms_page_changelist + page_id + '/edit-plugin/'+ plugin_id+ '/?popup=true&no_preview',
            padding: 0,
            minWidth: 800,
            minHeight: 300,
            height: 400,
            closeButton: '<a class="cms_toolbar_button cms_toolbar_iconbutton nyroModalClose" href="#" id="closeBut"><span><strong>Close</strong></span></a>'
        });
        /*
            css: {
                content: {
                    overflow: 'hidden'
                }
            }
         */
    }        

    function closeCMStoolbar(){
        $("#cms_toolbar").slideUp();                
        $("#cms_toolbar_mini").show();
        $("#cms_toolbar_spacer").slideUp();
        $.cookie("CMStoolbarColsed", "true", {path:'/', expires:7 });
        hideCMStoolbarSubmenus();
        resetBodyBackgroundPos();
    }

    function openCMStoolbar(){
        $("#cms_toolbar").slideDown();                
        $("#cms_toolbar_mini").hide();
        $("#cms_toolbar_spacer").slideDown();
        $.cookie("CMStoolbarColsed", "false", {path:'/', expires:7 });
        initBodyBackgroundPos();
    }

    function hideCMSToolbar(){
        $("#cms_toolbar").hide();
        $("#cms_toolbar_mini").show();
        $("#cms_toolbar_spacer").hide();
        resetBodyBackgroundPos(0);
    }
    function showCMSToolbar(){
        $("#cms_toolbar").show();
        $("#cms_toolbar_mini").hide();
        $("#cms_toolbar_spacer").show();        
        initBodyBackgroundPos(0);                        
    }

    function initBodyBackgroundPos(s){
        if(bodyBackgroundPosUnit=="px"){
            if(s==undefined){s=400;}
            var bodyBackgroundPosYnew = Number(bodyBackgroundPosY)+41;
            var bodyBackgroundPosYnew = ""+bodyBackgroundPosYnew;
            if ($.browser.msie) {//for IE
                $("body").css("background-position-x",bodyBackgroundPosXFull);
                $("body").css("background-position-y",bodyBackgroundPosYnew+"px");
            }else {
                $("body").stop().animate({backgroundPosition: "(" + bodyBackgroundPosXFull + " " + bodyBackgroundPosYnew + "px)"}, s);
            }            
        }            
    }
    function resetBodyBackgroundPos(s){
        if(bodyBackgroundPosUnit=="px") {
            if(s==undefined){s=400;}
            if ($.browser.msie){//for IE
                $("body").css("background-position-x",bodyBackgroundPosXFull);
                $("body").css("background-position-y",bodyBackgroundPosYFull);
            }else{
                $("body").stop().animate({backgroundPosition: "("+bodyBackgroundPosXFull+" "+bodyBackgroundPosY+"px)"},s);
            }            
        }else{
            if ($.browser.msie){//for IE
                $("body").css("background-position-x",bodyBackgroundPosXFull);
                $("body").css("background-position-y",bodyBackgroundPosYFull);
            }else{
                $("body").css("background-position",bodyBackgroundPos)
            }                                
        }
    }

    function hideCMStoolbarSubmenus(){            
        $(".cms_toolbar_submenubutton").removeClass("open");
    }

    $(document).ready(function () {
        bodyBackgroundPos = $("body").css("background-position");            
        if (bodyBackgroundPos == 'undefined' || bodyBackgroundPos == null) {
            //for IE
            bodyBackgroundPosXFull = $("body").css("background-position-x");
            bodyBackgroundPosYFull = $("body").css("background-position-y");                
            bodyBackgroundPos = bodyBackgroundPosXFull+" "+bodyBackgroundPosYFull;
        } else {
            bodyBackgroundPosXFull = bodyBackgroundPos.split(" ")[0];
            bodyBackgroundPosYFull = bodyBackgroundPos.split(" ")[1];
        }            

        bodyBackgroundPosUnit = bodyBackgroundPosYFull.substr(bodyBackgroundPosYFull.length-1, bodyBackgroundPosYFull.length);
    
        if(bodyBackgroundPosUnit=="%"){
            bodyBackgroundPosY = bodyBackgroundPosYFull.substr(0, bodyBackgroundPosYFull.length-1);
        }else{
            bodyBackgroundPosUnit = "px";
            bodyBackgroundPosY = bodyBackgroundPosYFull.substr(0, bodyBackgroundPosYFull.length-2);                
        }
        if(bodyBackgroundPosYFull == "0%" || bodyBackgroundPosYFull == "top"){
            bodyBackgroundPosUnit = "px";
            bodyBackgroundPosY = 0;
        }
    
        if ($.cookie("CMStoolbarColsed") == "true") {
            hideCMSToolbar();
        }else{
            showCMSToolbar();
        }            
    
          $(document).bind('click', function(e){     
            var cmsClicked = $(e.target);
            var cmsSubmenuHit = false;
            if(cmsClicked.parent().is('.cms_toolbar_submenubutton')){
                cmsClicked = $(cmsClicked.parent())
            }
            if(cmsClicked.parent().parent().is('.cms_toolbar_submenubutton')){
                cmsClicked = $(cmsClicked.parent().parent())
            }                
            if(cmsClicked.is('.cms_toolbar_submenubutton')) {
                cmsSubmenuHit = true;
                wasOpen = false;                    
                if(cmsClicked.hasClass("open")){wasOpen = true;}                                        
                hideCMStoolbarSubmenus();                    
                if(wasOpen == false){
                    cmsClicked.addClass("open");                                                
                
                    cmsClicked.find("ul").width("auto")
                    cmsClicked.find("li a").width("auto")
                    var maxW = 0;
                    cmsClicked.find("li a").each(function(){
                        if ($(this).width() > maxW)
                             maxW = $(this).width();
                    });    
                    cmsClicked.find("li a").width((maxW)+"px")                        
                    cmsClicked.find("ul").width((maxW+40)+"px")
                    
                    if(cmsClicked.hasClass("cms_toolbar_submenuselect")){
                        if(cmsClicked.find("ul").height()>=200){
                            cmsClicked.find("ul").css({height:"200px",width:(maxW+35)+"px"})
                        }
                    }
                
                }
            }
            if(cmsSubmenuHit == false){
                hideCMStoolbarSubmenus();
            }
        });    

        $("#cms_toolbar_edit_button_on").click(function(){
            var url = remove_from_url(window.location.href, "edit");
            url = insert_into_url(url, "edit-off", "");
            window.location = url;
            return false;
        });

        $("#cms_toolbar_edit_button_off").click(function(){
            window.location = insert_into_url(window.location.href, "edit", "");
            return false;
        });
    
        $("#cms_toolbar_closebutton").click(function () {
            closeCMStoolbar();        
            return false; 
        });
    
        $("#cms_toolbar_openbutton").click(function () {
            openCMStoolbar();            
            return false; 
        });            
    
        $("a.cms_toolbar_plugin_edit").click(function () {
            edit_plugin(page_id, plugin_id);
            return false;
        });

        $("a.cms_toolbar_downbutton").click(function () {
            move(1);
            return false;
        });

        $("a.cms_toolbar_upbutton").click(function () {
            move(-1);
            return false;
        });        
        $("#cms_toolbar_loginform a.cms_toolbar_button").click(function () {                
            $("#cms_toolbar_loginform .cms_submit").trigger("click");
            return false;
        });                
        $("#cms_toolbar_logoutform a.cms_toolbar_button").click(function () {                
            $("#cms_toolbar_logoutform .cms_submit").trigger("click");
            return false;
        });
    
    
        $(".cms_plugin_holder").each(function (i) {                
            var cmsPluginHolderFirstObj = $(this).children().eq(0)                
            $(this).css({
                float:cmsPluginHolderFirstObj.css("float"),
                clear:cmsPluginHolderFirstObj.css("clear")
            })
          });    

        if (page_is_defined) {
             $("#cms_toolbar_templatebutton li a").click(function(){
                 template = $(this).attr("href").split("#")[1];
                 $.post(urls.cms_page_change_template, {template:template}, function(){
                     window.location = window.location.href;
                     });
                 hideCMStoolbarSubmenus();
                 return false;
             });        
        }
    
        /* PLUGIN */            
        $("a.cms_toolbar_move_slot").live("click", function(){
            var target = $(this).attr("rel")
            $.post(
                urls.cms_page_move_plugin,
                { placeholder: target, plugin_id: plugin_id },
                function(data){
                    window.location = window.location.href;
                });
            return false;
        });
    
        $.fn.makeoverlay = function(options){
            var pluginH = $(this).height();
            var pluginHmin = 10;                
            if(pluginH<pluginHmin){pluginH=pluginHmin}                
            $(options).show();
            $(options).css({
                'width'        : $(this).width()+'px',
                'height'    : pluginH+'px',
                'left'        : $(this).offset().left+'px',
                'top'        : $(this).offset().top+'px'
            })
            if(options == "#cms_plugin_overlay2"){
                $(options).fadeIn(0);
                $(options).fadeOut(800, function () {
                    $(options).hide();
                })
            }
        }
            
        $(".cms_plugin_holder").live("mouseover", function(){    
            var splits = $(this).attr("id").split("_");
            page_id = splits[2];
            plugin_id = splits[3];
            placeholder = $(this).attr("rel");
            plugin_type = $(this).attr("type");    
        
            $(this).makeoverlay("#cms_plugin_overlay");
        
            $("div.cms_toolbar_plugintools_holder ul.cms_toolbar_submenu li:not(:last)").remove();
            var last = $("div.cms_toolbar_plugintools_holder ul.cms_toolbar_submenu li.last")
            var first = true;
            for(var i = 0; i < placeholder_data.length; i++){
                var data = placeholder_data[i];
                var found = false;
                if(data.type != placeholder){
                    for(j = 0; j < data.plugins.length; j++){
                        if(data.plugins[j] == plugin_type){
                            found = true;
                        }
                    }
                }
                if(found){
                    var html = '<li class="%(extra_class)s"><a class="cms_toolbar_move_slot" href="#" rel="%(type)s">' + translations.move_slot + '</a></li>'
                    if (first){
                        first = false;
                        html = html.split("%(extra_class)s").join("first")
                    }else{
                        html = html.split("%(extra_class)s").join("")
                    }
                    html = html.split("%(name)s").join(data.name)
                    html = html.split("%(type)s").join(data.type)
                    last.before(html)
                }
            }
        
        });            
    
        $("#cms_plugin_overlay").mouseenter(function(){
            $("#cms_plugin_overlay").show();
        }).mouseleave(function(){
            $("#cms_plugin_overlay").hide();
            hideCMStoolbarSubmenus();
        });
    
        $("div.cms_toolbar_placeholder_plugins li a").click(function(e){
            var select = $(this);
            var pluginvalue = select.attr('rel');
            var div = $(this).parent().parent().parent().parent().parent().parent();
            var placeholder = div.attr("rel")
            var splits = div.attr("id").split("cms_placeholder_")[1].split("_");
            var page_id = splits[1];
            var language = splits[0];
            if (!language) {
                alert("Unable to determine the correct language for this plugin! Please report the bug!");
            }
            if (pluginvalue) {
                var pluginname = select.children('[selected]').text();
                $.post(urls.cms_page_add_plugin, { page_id:page_id, placeholder:placeholder, plugin_type:pluginvalue, language:language }, function(data){
                    if ('error' != data) {
                        edit_plugin(page_id, data);
                    }
                }, "html" );
            }    
            hideCMStoolbarSubmenus();
            return false;
        });
    
        $("a.cms_toolbar_plugin_delete").click(function(){
            var question = translations.question; 
            var answer = confirm(question, true);
            if(answer){
                $.post(urls.cms_page_remove_plugin, { plugin_id:plugin_id }, function(data){
                    window.location = window.location.href;
                }, "html");
            }
            hideCMStoolbarSubmenus();
            return false;
        });
    });
});

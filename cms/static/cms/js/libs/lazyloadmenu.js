(function($) {
    $(function() {
        admin_base_url = document.URL.split("/cms/page/")[0] + "/";
        $(".tree-default li").click(function(event) { 
            var target = event.target;
            var page_id = $(target).attr("id").split("page_")[1];
            var load_nav_url = admin_base_url + "cms/page/" + page_id + "/load-nav/";
            if($(target).hasClass("closed")) {
                if($(target).children('ul').children('li').length == 0) {
                    $.get(load_nav_url, {}, function(r, status) {
                        $(target).children('ul').append(r);    
                    });
                }
            } 
        });
    });
})(jQuery.noConflict());
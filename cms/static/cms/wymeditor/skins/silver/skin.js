/* This file is part of the Silver skin for WYMeditor by Scott Edwin Lewis */

jQuery.fn.selectify = function() {
    return this.each(function() {
        jQuery(this).hover(
            function() {
                jQuery("h2", this).css("background-position", "0px -18px");
                jQuery("ul", this).fadeIn("fast");
            },
		    function() {
		        jQuery("h2", this).css("background-position", "");
		        jQuery("ul", this).fadeOut("fast");
		    }
        );
    });
};

WYMeditor.SKINS.silver = {

    init: function(wym) {

        //add some elements to improve the rendering
        jQuery(wym._box)
          .append('<div class="clear"></div>')
          .wrapInner('<div class="wym_inner"></div>');

        //render following sections as panels
        jQuery(wym._box).find(wym._options.classesSelector)
          .addClass("wym_panel");

        //render following sections as buttons
        jQuery(wym._box).find(wym._options.toolsSelector)
          .addClass("wym_buttons");

        //render following sections as dropdown menus
        jQuery(wym._box).find(wym._options.containersSelector)
          .addClass("wym_dropdown")
          .selectify();

        // auto add some margin to the main area sides if left area
        // or right area are not empty (if they contain sections)
        jQuery(wym._box).find("div.wym_area_right ul")
          .parents("div.wym_area_right").show()
          .parents(wym._options.boxSelector)
          .find("div.wym_area_main")
          .css({"margin-right": "155px"});

        jQuery(wym._box).find("div.wym_area_left ul")
          .parents("div.wym_area_left").show()
          .parents(wym._options.boxSelector)
          .find("div.wym_area_main")
          .css({"margin-left": "155px"});

        //make hover work under IE < 7
        jQuery(wym._box).find(".wym_section").hover(function(){
          jQuery(this).addClass("hover");
        },function(){
          jQuery(this).removeClass("hover");
        });
    }
};

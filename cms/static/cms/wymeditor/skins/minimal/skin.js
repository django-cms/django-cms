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

WYMeditor.SKINS.minimal = {
    //placeholder for the skin JS, if needed

    //init the skin
    //wym is the WYMeditor.editor instance
    init: function(wym) {

        //render following sections as dropdown menus
        jQuery(wym._box).find(wym._options.toolsSelector + ', ' + wym._options.containersSelector + ', ' + wym._options.classesSelector)
          .addClass("wym_dropdown")
          .selectify();


    }
};

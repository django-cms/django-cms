/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
var CMS = window.CMS || {};

// #############################################################################
// MODAL
(function ($) {
    'use strict';

    // shorthand for jQuery(document).ready();
    $(function () {
        /**
         * TODO
         *
         * @class PageTree
         * @namespace CMS
         * @uses CMS.API.Helpers
         */
        CMS.PageTree = new CMS.Class({

            implement: [CMS.API.Helpers],

            initialize: function initialize() {
                this.container = $('.js-cms-pagetree');
                this.options = this.container.data('json');

                this.container.jstree(

{
"core" : {
"animation" : 0,
"check_callback" : true,
"themes" : { "stripes" : true },
'data' : {
'url' : function (node) {
return node.id === '#' ?
'ajax_demo_roots.json' : 'ajax_demo_children.json';
},
'data' : function (node) {
return { 'id' : node.id };
}
}
},
"types" : {
"#" : {
"max_children" : 1,
"max_depth" : 4,
"valid_children" : ["root"]
},
"root" : {
"icon" : "/static/3.2.1/assets/images/tree_icon.png",
"valid_children" : ["default"]
},
"default" : {
"valid_children" : ["default","file"]
},
"file" : {
"icon" : "glyphicon glyphicon-file",
"valid_children" : []
}
},
"plugins" : [
"contextmenu", "dnd", "search",
"state", "types", "wholerow"
]
}


                );

                console.log(this.options);







            }
        });

        // autoload the pagetree
        new CMS.PageTree();


    });

})(CMS.$);

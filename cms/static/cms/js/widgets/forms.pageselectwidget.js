/*
 * Copyright https://github.com/divio/django-cms
 */

// this essentially makes sure that dynamically required bundles are loaded
// from the same place
// eslint-disable-next-line
__webpack_public_path__ = require('../modules/get-dist-path')('bundle.forms.pageselectwidget');

// #############################################################################
// PAGE SELECT WIDGET
// cms/forms/widgets.py
require.ensure(
    [],
    function(require) {
        var $ = require('jquery');
        var Class = require('classjs');

        /**
         * Manages the selection of two select fields. The first field
         * sets the "Site" and the second the "Pagetree".
         *
         * @class PageSelectWidget
         * @namespace CMS
         */
        var PageSelectWidget = new Class({
            initialize: function initialize(options) {
                this.options = $.extend(true, {}, this.options, options);
                // load functionality
                this._setup(options);
            },

            /**
             * Setup internal functions and events.
             *
             * @private
             * @method _setup
             * @param {Object} options
             * @param {String} options.name
             */
            _setup: function _setup(options) {
                var group0 = $('#id_' + options.name + '_0');
                var group1 = $('#id_' + options.name + '_1');
                var group2 = $('#id_' + options.name + '_2');
                var tmp;

                // handles the change event on the first select "site"
                // that controls the display of the second select "pagetree"
                group0
                    .on('change', function() {
                        tmp = $(this).children(':selected').text();

                        group1.find('optgroup').remove();
                        group1.append(group2.find('optgroup[label="' + tmp + '"]').clone()).change();

                        // refresh second select
                        setTimeout(function() {
                            group1.trigger('change');
                        }, 0);
                    })
                    .trigger('change');

                // sets the correct value
                group1.on('change', function() {
                    tmp = $(this).find('option:selected').val();

                    if (tmp) {
                        group2.find('option').prop('selected', false);
                        group2.find('option[value="' + tmp + '"]').prop('selected', true);
                    } else if (group2.length) {
                        group2.find('option[value=""]').prop('selected', true);
                    }
                });

                // don't allow to add another page from in here
                $('#add_id_' + options.name).hide();
            }
        });

        window.CMS = window.CMS || {};
        window.CMS.PageSelectWidget = PageSelectWidget;

        // init
        $(function() {
            window.CMS.Widgets._pageSelectWidgets.forEach(function(widget) {
                new PageSelectWidget(widget);
            });
        });
    },
    'admin.widget'
);

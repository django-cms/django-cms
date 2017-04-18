/*
 * Copyright https://github.com/divio/django-cms
 */

// this essentially makes sure that dynamically required bundles are loaded
// from the same place
// eslint-disable-next-line
__webpack_public_path__ = require('../modules/get-dist-path')('bundle.forms.apphookselect');

// #############################################################################
// APP HOOK SELECT
require.ensure([], function (require) {
    var $ = require('jquery');
    var apphooks_configuration = window.apphooks_configuration || {};

    // shorthand for jQuery(document).ready();
    $(function () {
        var appHooks = $('#application_urls');
        var selected = appHooks.find('option:selected');
        var appNsRow = $('.form-row.application_namespace');
        var appNs = appNsRow.find('#id_application_namespace');
        var appCfgsRow = $('.form-row.application_configs');
        var appCfgs = appCfgsRow.find('#application_configs');
        var appCfgsAdd = appCfgsRow.find('#add_application_configs');
        var original_ns = appNs.val();

        // Shows / hides namespace / config selection widgets depending on the user input
        appHooks.setupNamespaces = function () {
            var opt = $(this).find('option:selected');

            if ($(appCfgs).length > 0 && apphooks_configuration[opt.val()]) {
                appCfgs.html('');
                for (var i = 0; i < apphooks_configuration[opt.val()].length; i++) {
                    var selectedCfgs = '';

                    if (apphooks_configuration[opt.val()][i][0] === window.apphooks_configuration_value) {
                        selectedCfgs = 'selected="selected"';
                    }
                    appCfgs.append(
                        '<option ' + selectedCfgs + ' value="' + apphooks_configuration[opt.val()][i][0] + '">' +
                            apphooks_configuration[opt.val()][i][1] +
                        '</option>'
                    );
                }
                appCfgsAdd.attr('href', window.apphooks_configuration_url[opt.val()] +
                    // Here we check if we are on django>=1.8 by checking if the method introduced in that version
                    // exists, and if it does - we add `_popup` ourselves, because otherwise the popup with
                    // apphook creation form will not be dismissed correctly
                    (window.showRelatedObjectPopup ? '?_popup=1' : ''));
                appCfgsRow.removeClass('hidden');
                appNsRow.addClass('hidden');
            } else {
                appCfgsRow.addClass('hidden');
                if (opt.data('namespace')) {
                    appNsRow.removeClass('hidden');
                } else {
                    appNsRow.addClass('hidden');
                }
            }
        };

        // Hide the namespace widgets if its not required.
        appHooks.setupNamespaces();

        // Show it if we change to an app_hook that requires a namespace
        appHooks.on('change', function () {
            var self = $(this);
            var opt = self.find('option:selected');

            appHooks.setupNamespaces();

            // If we clear the app_hook, clear out the app_namespace too
            if (!self.val()) {
                appNs.val('');
                appNs.removeAttr('value');
            }

            // When selecting back the original apphook we try
            // to restore the original configuration
            if (selected.val() === opt.val()) {
                if (original_ns) {
                    appNs.val(original_ns);
                }
            } else if (opt.data('namespace')) {
                // If new apphook has a namespace, suggest the default
                appNs.val(opt.data('namespace'));
            } else {
                // Cleanup the whole thing
                appNs.val('');
                appNs.removeAttr('value');
            }
        });

    });
}, 'admin.widget');

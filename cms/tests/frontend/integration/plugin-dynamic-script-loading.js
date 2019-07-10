'use strict';

// #############################################################################
// Edit page content

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var cms = helpers(casperjs);

var include_lists = [
    [false, false, false, false],
    [false, false, false, true],
    [false, false, true, false],
    [false, false, true, true],
    [false, true, false, false],
    [false, true, false, true],
    [false, true, true, false],
    [false, true, true, true],
    [true, false, false, false],
    [true, false, false, true],
    [true, false, true, false],
    [true, false, true, true],
    [true, true, false, false],
    [true, true, false, true],
    [true, true, true, false],
    [true, true, true, true]
];

var full_class_list = [
    'cms-execute-js-to-render',
    'cms-trigger-event-document-DOMContentLoaded',
    'cms-trigger-event-window-DOMContentLoaded',
    'cms-trigger-event-window-load'
];

var element_id_list = [
    ['#inline_no_trigger', '#from_src_no_trigger'],
    ['#inline_needs_trigger_document_DOMContentLoaded', '#from_src_needs_trigger_document_DOMContentLoaded'],
    ['#inline_needs_trigger_window_DOMContentLoaded', '#from_src_needs_trigger_window_DOMContentLoaded'],
    ['#inline_needs_trigger_window_load', '#from_src_needs_trigger_window_load']
];

/**
 * Counts the number of h2 tags and returns their amount.
 * @returns {number}
 */
function count_h2_tags() {
    var h2_tags = document.querySelectorAll('h2');
    return h2_tags.length;
}

/**
 * Generates a string of the used classes, to prompt during test
 *
 * @param {boolean[]} include_list subset of include_lists
 *
 * @returns {string} string representation of the used classes
 */
function gennerate_class_list_string(include_list) {
    var i;
    var class_list = [];
    for (i = 0; i < include_list.length; i++) {
        if (include_list[i]) {
            class_list.push(full_class_list[i]);
        }
    }
    return '[' + String(class_list) + ']';
}

/**
 * Tests for existence/none existence of elements given by the css selectors,
 * depending on the given condition
 *
 * @param {casper.test} test    test object that is needed for the tests
 * @param {boolean} exist_condition     condition if the test should check existence or none existence
 * @param {string[]} selectors  array of css selectors
 */
function test_element_exists(test, exist_condition, selectors) {
    var i;
    for (i = 0; i < selectors.length; i++) {
        if (exist_condition) {
            test.assertExists(selectors[i]);
        } else {
            test.assertDoesntExist(selectors[i]);
        }
    }
}

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function(done) {
    casper
        .start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

/**
 * Parametriced testfunction, testing all testcases, depending on its index.
 * See ./cms/test_utils/project/pluginapp/plugins/dynamic_js_loading
 *
 *
 * @param {number} test_case_index  Index of the testcase (testcase - 1)
 */
function parametrized_test(test_case_index) {
    // var include_list = [execute_js, document_content, window_content, window_load];
    var include_list = include_lists[test_case_index];
    var execute_js = include_list[0];
    var document_content = include_list[1];
    var window_content = include_list[2];
    var window_load = include_list[3];

    var nr_of_used_classes = include_list.reduce(function(a, b) {
        return Number(a) + Number(b);
    }, 0);
    var nr_of_elements = 2 * nr_of_used_classes * Number(execute_js);
    var class_list_string = gennerate_class_list_string(include_list);

    casper.test.begin('Test dynamic loading of scripts with classes ' + class_list_string, function(test) {
        casper
            .start(globals.editUrl)
            .then(
                cms.addPlugin({
                    type: 'DynamicJsLoadingPlugin',
                    content: {
                        id_testcase: String(test_case_index + 1)
                    }
                })
            )
            .then(cms.switchTo('content'))
            .waitForSelector('h1', function() {
                test.assertSelectorHasText(
                    '#dynamic_js_loading_heading',
                    'Test dynamic loading of testcase ' + String(test_case_index + 1)
                );
            })
            .wait(200, function() {
                test.assertEvalEquals(
                    count_h2_tags,
                    nr_of_elements,
                    'Counts the by js code generated h2 tags in edit mode'
                );
                test_element_exists(test, execute_js, element_id_list[0]);
                test_element_exists(test, execute_js && document_content, element_id_list[1]);
                test_element_exists(test, execute_js && window_content, element_id_list[2]);
                test_element_exists(test, execute_js && window_load, element_id_list[3]);
            })
            .reload(function() {
                this.echo('Page reloaded');
            })
            .waitForSelector('h2', function() {
                test.assertEvalEquals(count_h2_tags, 8, 'Counts the by js code generated h2 tags after a reload');
                var i;
                for (i = 0; i < element_id_list.length; i++) {
                    test_element_exists(test, true, element_id_list[i]);
                }
            })
            .run(function() {
                test.done();
            });
    });
}

var i;
for (i = 0; i < include_lists.length; i++) {
    parametrized_test(i);
}

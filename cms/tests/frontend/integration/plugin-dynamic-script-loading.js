'use strict';

// #############################################################################
// Edit page content

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var cms = helpers(casperjs);

/**
 * Counts the number of h2 tags and returns their amount.
 * @returns {number}
 */
function count_h2_tags() {
    var h2_tags = document.querySelectorAll('h2');
    return h2_tags.length;
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

casper.test.begin(
    'Test dynamic loading of scripts with classes "cms-execute-js-to-render" and "cms-trigger-load-events" ',
    function(test) {
        casper
            .start(globals.editUrl)
            .then(
                cms.addPlugin({
                    type: 'DynamicJsLoadingPlugin',
                    content: {
                        id_testcase: '1'
                    }
                })
            )
            .then(cms.switchTo('content'))
            .waitForSelector('h1', function() {
                test.assertSelectorHasText('#dynamic_js_loading_heading', 'Test dynamic loading of testcase 1');
            })
            .waitForSelector('h2', function() {
                test.assertEvalEquals(count_h2_tags, 4, 'Counts the by js code generated h2 tags');
                test.assertExists('#inline_no_trigger');
                test.assertExists('#inline_needs_trigger');
                test.assertExists('#from_src_no_trigger');
                test.assertExists('#from_src_needs_trigger');
            })
            .reload(function() {
                this.echo('Page reloaded');
            })
            .waitForSelector('h2', function() {
                test.assertEvalEquals(count_h2_tags, 4, 'Counts the by js code generated h2 tags');
                test.assertExists('#inline_no_trigger');
                test.assertExists('#inline_needs_trigger');
                test.assertExists('#from_src_no_trigger');
                test.assertExists('#from_src_needs_trigger');
            })
            .run(function() {
                test.done();
            });
    }
);

casper.test.begin('Test dynamic loading of scripts with only class "cms-execute-js-to-render"', function(test) {
    casper
        .start(globals.editUrl)
        .then(
            cms.addPlugin({
                type: 'DynamicJsLoadingPlugin',
                content: {
                    id_testcase: '2'
                }
            })
        )
        .then(cms.switchTo('content'))
        .waitForSelector('h1', function() {
            test.assertSelectorHasText('#dynamic_js_loading_heading', 'Test dynamic loading of testcase 2');
        })
        .waitForSelector('h2', function() {
            test.assertEvalEquals(count_h2_tags, 2, 'Counts the by js code generated h2 tags');
            test.assertExists('#inline_no_trigger');
            test.assertDoesntExist('#inline_needs_trigger');
            test.assertExists('#from_src_no_trigger');
            test.assertDoesntExist('#from_src_needs_trigger');
        })
        .reload(function() {
            this.echo('Page reloaded');
        })
        .waitForSelector('h2', function() {
            test.assertEvalEquals(count_h2_tags, 4, 'Counts the by js code generated h2 tags');
            test.assertExists('#inline_no_trigger');
            test.assertExists('#inline_needs_trigger');
            test.assertExists('#from_src_no_trigger');
            test.assertExists('#from_src_needs_trigger');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Test dynamic loading of scripts with only class "cms-trigger-load-events"', function(test) {
    casper
        .start(globals.editUrl)
        .then(
            cms.addPlugin({
                type: 'DynamicJsLoadingPlugin',
                content: {
                    id_testcase: '3'
                }
            })
        )
        .then(cms.switchTo('content'))
        .waitForSelector('h1', function() {
            test.assertSelectorHasText('#dynamic_js_loading_heading', 'Test dynamic loading of testcase 3');
        })
        .wait(3000, function() {
            test.assertEvalEquals(count_h2_tags, 0, 'Counts the by js code generated h2 tags');
        })
        .reload(function() {
            this.echo('Page reloaded');
        })
        .waitForSelector('h2', function() {
            test.assertEvalEquals(count_h2_tags, 4, 'Counts the by js code generated h2 tags');
            test.assertExists('#inline_no_trigger');
            test.assertExists('#inline_needs_trigger');
            test.assertExists('#from_src_no_trigger');
            test.assertExists('#from_src_needs_trigger');
        })
        .run(function() {
            test.done();
        });
});

casper.test.begin('Test dynamic loading of scripts with no classes', function(test) {
    casper
        .start(globals.editUrl)
        .then(
            cms.addPlugin({
                type: 'DynamicJsLoadingPlugin',
                content: {
                    id_testcase: '4'
                }
            })
        )
        .then(cms.switchTo('content'))
        .waitForSelector('h1', function() {
            test.assertSelectorHasText('#dynamic_js_loading_heading', 'Test dynamic loading of testcase 4');
        })
        .wait(3000, function() {
            test.assertEvalEquals(count_h2_tags, 0, 'Counts the by js code generated h2 tags');
        })
        .reload(function() {
            this.echo('Page reloaded');
        })
        .waitForSelector('h2', function() {
            test.assertEvalEquals(count_h2_tags, 4, 'Counts the by js code generated h2 tags');
            test.assertExists('#inline_no_trigger');
            test.assertExists('#inline_needs_trigger');
            test.assertExists('#from_src_no_trigger');
            test.assertExists('#from_src_needs_trigger');
        })
        .run(function() {
            test.done();
        });
});

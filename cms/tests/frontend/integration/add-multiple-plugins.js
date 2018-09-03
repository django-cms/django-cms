var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var casperjs = require('casper');
var cms = helpers(casperjs);

casper.test.setUp(function(done) {
    casper
        .start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Tooltip is correct after adding multiple plugins', function(test) {
    casper
        .start(globals.editUrl)
        .then(cms.addPlugin({
            type: 'MultiWrapPlugin',
            content: {
                id_create: 1
            }
        }))
        .wait(1000, function () {
            var plugin = this.getElementBounds('.inner-wrap');

            this.mouse.move(plugin.left + plugin.width / 2, plugin.top + plugin.height / 2);
        })
        .then(function () {
            test.assertVisible('.cms-tooltip');
            test.assertSelectorHasText(
                '.cms-tooltip span',
                'Placeholder_Content_1: Wrap'
            );
        })
        .run(function() {
            test.done();
        });
});

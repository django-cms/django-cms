'use strict';

// #############################################################################
// Drag'n'drop plugins

var globals = require('./settings/globals');
var cms = require('./helpers/cms')();


casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

casper.test.begin('Drag plugin to another placeholder', function (test) {
    casper.start(globals.editUrl)
        .then(function () {
            casper.echo('Hi');
        })
        .run(function () {
            test.done();
        });
});

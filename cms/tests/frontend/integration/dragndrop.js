'use strict';

// #############################################################################
// Drag'n'drop plugins

var globals = require('./settings/globals');
var casperjs = require('casper');
var cms = require('./helpers/cms')(casperjs);

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        // .then(cms.addPage({ title: 'First page' }))
        // actually creates 3 plugins - row > col + col
        .then(cms.addPlugin({
            type: 'GridPlugin',
            content: {
                id_create: 2,
                id_create_size: 12
            }
        }))
        .then(cms.addPlugin({
            type: 'TextPlugin',
            content: {
                id_body: 'Test text'
            }
        }))
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.removePage())
        // .then(cms.logout())
        .run(done);
});

casper.test.begin('Drag plugin to another placeholder', function (test) {
    casper.start(globals.editUrl)
        .then(function () {
            test.assertElementCount('.cms-structure .cms-draggable', 4);
        })
        .run(function () {
            test.done();
        });
});

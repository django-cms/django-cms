require('./../casperjs.conf').init();

casper.test.begin('Sample test', function (test) {
    'use strict';

    casper
        .start('http://www.google.com/', function () {
            test.assertTitle('Google', 'google.com has the correct title');
        })
        .run(function () {
            test.done();
        });
});

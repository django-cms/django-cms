'use strict';

require('./../casperjs.conf').init();

casper.test.begin('Sample test', function (test) {
    casper
        .start('http://www.google.com/', function () {
            test.assertTitle('Google', 'google.com has the correct title');
        })
        .run(function () {
            test.done();
        });
});

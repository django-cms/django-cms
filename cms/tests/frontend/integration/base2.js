'use strict';

casper.test.begin('Sample test 2', function (test) {
    casper
        .start('http://www.google.com/', function () {
            test.assertTitle('Google', 'google.com has the correct title');
        })
        .run(function () {
            test.done();
        });
});

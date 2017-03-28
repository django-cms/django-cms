var gutil = require('gulp-util');
var spawn = require('child_process').spawn;
var path = require('path');

module.exports = function (gulp, opts) {
    var pathToCasper = opts.pathToCasper || path.join(__dirname, '../../..', 'node_modules/.bin/casperjs');
    var pathToPhantom = opts.pathToPhantom || require('phantomjs-prebuilt').path;
    var tests = opts.argv.tests ? opts.argv.tests : '*';

    process.env.PHANTOMJS_EXECUTABLE = pathToPhantom;

    return function (done) {
        var casperChild;

        if (tests !== '*') {
            gutil.log('Running tests for ' + tests);
        }

        casperChild = spawn(
            pathToCasper,
            ['test', '--web-security=no']
            .concat(['--tests=' + tests])
            .concat([path.join(__dirname, '../../../tests/integration/index.bundle.js')])
        );

        casperChild.stdout.on('data', function (data) {
            gutil.log('CasperJS:', data.toString().slice(0, -1)); // eslint-disable-line no-magic-numbers
        });

        casperChild.on('close', function (code) {
            done(code);
        });
    };
};

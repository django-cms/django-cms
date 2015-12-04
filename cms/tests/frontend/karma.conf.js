/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * http://github.com/aldryn/aldryn-boilerplate-bootstrap3
 */
// jshint node: true
'use strict';

var baseConf = require('./base.conf');
var argv = require('minimist')(process.argv.slice(2));

module.exports = function (config) {

    var files = ['*'];
    if (argv && argv.tests) {
        files = argv.tests.split(',');
        console.log('Running tests for ' + files.join(', '));
    }

    var useSauceLabs = function () {
        var val = process.env.SKIP_SAUCE_LABS;
        return val !== undefined &&
            val === '0' &&
            process.env.SAUCE_USERNAME &&
            process.env.SAUCE_ACCESS_KEY;
    };

    var browsers = {
        'PhantomJS': 'used for local testing'
    };

    // Browsers to run on Sauce Labs
    // Check out https://saucelabs.com/platforms for all browser/OS combos
    if (useSauceLabs()) {
        browsers = baseConf.sauceLabsBrowsers.reduce(function (browsers, capability) {
            browsers[JSON.stringify(capability)] = capability;
            browsers[JSON.stringify(capability)].base = 'SauceLabs';
            return browsers;
        }, {});
    }

    var settings = {
        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '../../..',

        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['jasmine', 'fixture', 'phantomjs-shim'],

        // list of files / patterns to load in the browser
        files: [
            // these have to be specified in order since
            // dependency loading is not handled yet
            'cms/static/cms/js/libs/jquery.min.js',
            'cms/static/cms/js/libs/class.min.js',
            'cms/static/cms/js/libs/pep.js',
            'cms/static/cms/js/modules/jquery.ui.custom.js',
            'cms/static/cms/js/modules/jquery.ui.touchpunch.js',
            'cms/static/cms/js/modules/jquery.ui.nestedsortable.js',
            'cms/static/cms/js/modules/cms.base.js',
            'cms/static/cms/js/modules/jquery.transition.js',
            'cms/static/cms/js/modules/cms.messages.js',
            'cms/static/cms/js/modules/cms.modal.js',
            'cms/static/cms/js/modules/cms.sideframe.js',
            'cms/static/cms/js/modules/cms.clipboard.js',
            'cms/static/cms/js/modules/cms.plugins.js',
            'cms/static/cms/js/modules/cms.structureboard.js',
            'cms/static/cms/js/modules/cms.navigation.js',
            'cms/static/cms/js/modules/cms.toolbar.js',
            'cms/static/cms/js/modules/cms.tooltip.js',

            // test helpers
            'cms/tests/frontend/unit/helpers/mock-ajax.js'
        ].concat(
            // tests themselves
            files.map(function (pattern) {
                return 'cms/tests/frontend/unit/' + pattern + '.test.js';
            })
        ),

        // list of files to exclude
        exclude: [
            'cms/static/cms/js/dist/*.js'
        ],

        // preprocess matching files before serving them to the browser
        // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
        preprocessors: {
            'cms/static/cms/js/modules/cms.*': ['coverage'],
            '**/*.html': ['html2js']
        },

        // optionally, configure the reporter
        coverageReporter: {
            reporters: [
                { type: 'html', dir: 'cms/tests/frontend/coverage/' },
                { type: 'lcov', dir: 'cms/tests/frontend/coverage/' }
            ]
        },

        // fixtures dependency
        // https://github.com/billtrik/karma-fixture
        jsonFixturesPreprocessor: {
            variableName: '__json__'
        },

        // test results reporter to use
        // possible values: 'dots', 'progress'
        // available reporters: https://npmjs.org/browse/keyword/karma-reporter
        reporters: ['progress', 'coverage', 'saucelabs'].concat(process.env.CI ? ['coveralls'] : []),

        // web server port
        port: 9876,

        // enable / disable colors in the output (reporters and logs)
        colors: true,

        // level of logging
        // possible values:
        // config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
        logLevel: config.LOG_INFO,

        // enable / disable watching file and executing tests whenever any file changes
        autoWatch: true,

        // start these browsers
        browsers: Object.keys(browsers),

        concurrency: (function () {
            // travis
            if (useSauceLabs()) {
                return 3;
            } else {
                return Infinity;
            }
        })(),
        browserNoActivityTimeout: 50 * 1000,

        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: false
    };

    // saucelabs are disabled for the moment because there are numerous connection problems
    // between travis and sauce labs
    if (useSauceLabs()) {
        settings.sauceLabs = {
            testName: baseConf.formatTaskName('Unit')
        };
        settings.captureTimeout = 0; // rely on SL timeout, see karma-runner/karma-sauce-launcher#37
        settings.customLaunchers = browsers;
    }

    config.set(settings);
};

/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * http://github.com/aldryn/aldryn-boilerplate-bootstrap3
 */

'use strict';

var baseConf = require('./base.conf');
var argv = require('minimist')(process.argv.slice(2));

module.exports = function (config) {

    var files = ['*'];
    if (argv && argv.tests) {
        files = argv.tests.split(',');
        // eslint-disable-next-line
        console.log('Running tests for ' + files.join(', '));
    }

    var useSauceLabs = function () {
        var val = process.env.USE_SAUCE_LABS;
        return (val === undefined || val !== '0') && process.env.SAUCE_USERNAME && process.env.SAUCE_ACCESS_KEY;
    };

    var browsers = {
        PhantomJS: 'used for local testing'
    };

    var settings = {
        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '../../..',

        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['jasmine', 'fixture', 'phantomjs-shim'],

        // list of files / patterns to load in the browser
        files: [
            'cms/static/cms/css/cms.base.css',

            // these have to be specified in order since
            // dependency loading is not handled yet
            'cms/static/cms/js/polyfills/array.prototype.findindex.js',
            'cms/static/cms/js/libs/jquery.min.js',
            'cms/static/cms/js/libs/class.min.js',
            'cms/static/cms/js/libs/pep.js',
            'cms/static/cms/js/libs/jstree/jstree.min.js',
            'cms/static/cms/js/libs/jstree/jstree.grid.min.js',
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
            'cms/static/cms/js/modules/cms.pagetree.dropdown.js',
            'cms/static/cms/js/modules/cms.pagetree.stickyheader.js',
            'cms/static/cms/js/modules/cms.pagetree.js',

            // test helpers
            'cms/tests/frontend/unit/helpers/mock-ajax.js',
            'cms/tests/frontend/unit/helpers/jasmine-jquery.js',

            // fixtures
            'cms/tests/frontend/unit/fixtures/**/*.html',
            'cms/tests/frontend/unit/html/**/*.html',

            // other static assets
            { pattern: 'cms/static/cms/**/*.gif', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.woff', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.woff2', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.ttf', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.eot', watched: false, included: false, served: true }
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
            'cms/tests/frontend/unit/fixtures/**/*.html': ['html2js']
        },

        // optionally, configure the reporter
        coverageReporter: {
            instrumenterOptions: {
                istanbul: { noCompact: true }
            },
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
        reporters: ['dots', 'coverage', 'saucelabs'].concat(process.env.CI ? ['coveralls'] : []),

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

        concurrency: Infinity,

        // we need at least 2 minutes because things are a bit slow
        browserNoActivityTimeout: 2 * 60 * 1000,

        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: false
    };

    // saucelabs are disabled for the moment because there are numerous connection problems
    // between travis and sauce labs
    if (useSauceLabs()) {

        // Browsers to run on Sauce Labs
        // Check out https://saucelabs.com/platforms for all browser/OS combos
        browsers = baseConf.sauceLabsBrowsers.reduce(function (browsersMap, capability) {
            browsersMap[JSON.stringify(capability)] = capability;
            browsersMap[JSON.stringify(capability)].base = 'SauceLabs';
            return browsersMap;
        }, {});

        settings.browsers = Object.keys(browsers);

        if (process.env.CI) {
            settings.concurrency = 5;
        }

        settings.sauceLabs = {
            testName: baseConf.formatTaskName('Unit'),
            build: 'TRAVIS #' + process.env.TRAVIS_BUILD_NUMBER + ' (' + process.env.TRAVIS_BUILD_ID + ')',
            tunnelIdentifier: process.env.TRAVIS_JOB_NUMBER || String(Math.random())
        };
        settings.logLevel = config.LOG_ERROR;
        settings.captureTimeout = 0; // rely on SL timeout, see karma-runner/karma-sauce-launcher#37
        settings.customLaunchers = browsers;
    }

    config.set(settings);
};

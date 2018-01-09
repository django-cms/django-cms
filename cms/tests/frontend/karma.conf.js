/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * https://github.com/aldryn/aldryn-boilerplate-bootstrap3
 */

'use strict';

process.env.NODE_ENV = 'test';

var baseConf = require('./base.conf');
var path = require('path');
var fs = require('fs');
var argv = require('minimist')(process.argv.slice(2));
var webpack = require('webpack');
var webpackConfig = require('../../../webpack.config.js')({
    PROJECT_PATH: {
        js: path.join(__dirname, '../../../cms/static/cms/js')
    },
    debug: true
});

webpackConfig.module.rules.splice(1, 0, {
    test: /cms\/js\/modules\/(?!jquery).*.js$/,
    use: [{
        loader: 'istanbul-instrumenter-loader',
        query: {
            esModules: true,
            noCompact: true
        }
    }]
});

var files = ['*'];
if (argv && argv.tests) {
    files = argv.tests.split(',');
    // eslint-disable-next-line
    console.log('Running tests for ' + files.join(', '));
}

var CMS_VERSION = fs.readFileSync('cms/__init__.py', { encoding: 'utf-8' })
    .match(/__version__ = '(.*?)'/)[1];

webpackConfig.plugins = [
    new webpack.DefinePlugin({
        __DEV__: 'false',
        __TEST__: 'true',
        __CMS_VERSION__: JSON.stringify(CMS_VERSION),
        files: JSON.stringify(files)
    })
];

module.exports = function (config) {
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
            'cms/static/cms/css/' + CMS_VERSION + '/cms.base.css',

            // fixtures
            'cms/tests/frontend/unit/fixtures/**/*.html',
            'cms/tests/frontend/unit/html/**/*.html',
            'cms/tests/frontend/unit/index.js',

            // other static assets
            { pattern: 'cms/static/cms/**/*.gif', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.woff', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.woff2', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.ttf', watched: false, included: false, served: true },
            { pattern: 'cms/static/cms/**/*.eot', watched: false, included: false, served: true }
        ],

        // list of files to exclude
        exclude: [
            'cms/static/cms/js/dist/*.js',
            'cms/static/cms/js/*.js',
            'cms/static/cms/js/modules/*.js',
            'cms/static/cms/js/modules/jquery.*.js'
        ],

        // preprocess matching files before serving them to the browser
        // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
        preprocessors: {
            'cms/tests/frontend/unit/index.js': ['webpack', 'sourcemap'],
            'cms/static/cms/js/modules/*.js': ['sourcemap'],
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

        webpack: {
            cache: true,
            devtool: 'inline-source-map',
            resolve: webpackConfig.resolve,
            plugins: webpackConfig.plugins,
            module: webpackConfig.module
        },

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

/*
 * Copyright (c) 2013, django CMS Association
 * Licensed under BSD
 * https://github.com/django-cms/django-cms
 */

'use strict';

process.env.NODE_ENV = 'test';
process.env.CHROME_BIN = require('puppeteer').executablePath();


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
    var browsers = {
        ChromeHeadlessCI: 'used for local testing'
    };

    var settings = {
        // base path that will be used to resolve all patterns (eg. files, exclude)
        basePath: '../../..',

        // frameworks to use
        // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
        frameworks: ['webpack', 'jasmine', 'fixture'],

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
        reporters: ['dots', 'coverage'].concat(process.env.CI ? ['coveralls'] : []),

        webpack: {
            mode: 'development',
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

        customLaunchers: {
            ChromeHeadlessCI: {
                base: 'ChromeHeadless',
                flags: ['--window-size=1280,1080', '--no-sandbox']
            }
        },

        concurrency: Infinity,

        // we need at least 2 minutes because things are a bit slow
        browserNoActivityTimeout: 2 * 60 * 1000,

        // Continuous Integration mode
        // if true, Karma captures browsers, runs the tests and exits
        singleRun: false
    };


    config.set(settings);
};

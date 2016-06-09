var webpack = require('webpack');

module.exports = function (opts) {
    'use strict';

    var PROJECT_PATH = opts.PROJECT_PATH;
    var debug = opts.debug;

    var baseConfig = {
        devtool: false,
        watch: !!opts.watch,
        entry: {
            'toolbar': PROJECT_PATH.js + '/toolbar.js',
            'admin.base': PROJECT_PATH.js + '/admin.base.js',
            'admin.pagetree': PROJECT_PATH.js + '/admin.pagetree.js',
            'admin.changeform': PROJECT_PATH.js + '/admin.changeform.js'
        },
        output: {
            path: PROJECT_PATH.js + '/dist/',
            filename: 'bundle.[name].min.js',
            jsonpFunction: 'cmsWebpackJsonp'
        },
        plugins: [
            // this way admin.pagetree bundle won't
            // include deps already required in admin.base bundle
            new webpack.optimize.CommonsChunkPlugin({
                name: 'admin.base',
                chunks: ['admin.pagetree', 'admin.changeform']
            })
        ],
        resolve: {
            extensions: ['', '.js'],
            alias: {
                jquery: PROJECT_PATH.js + '/libs/jquery.min.js',
                classjs: PROJECT_PATH.js + '/libs/class.min.js',
                jstree: PROJECT_PATH.js + '/libs/jstree/jstree.min.js'
            }
        },
        module: {
            loaders: [
                {
                    test: /(modules\/jquery|libs\/pep)/,
                    loaders: [
                        'imports?jQuery=jquery'
                    ]
                },
                {
                    test: /class.min.js/,
                    loaders: [
                        'exports?Class'
                    ]
                }
            ]
        }
    };

    if (debug) {
        baseConfig.devtool = 'inline-source-map';
        baseConfig.plugins = baseConfig.plugins.concat([
            new webpack.NoErrorsPlugin(),
            new webpack.DefinePlugin({
                __DEV__: 'true'
            })
        ]);
    } else {
        baseConfig.plugins = baseConfig.plugins.concat([
            new webpack.DefinePlugin({
                __DEV__: 'false'
            }),
            new webpack.optimize.OccurenceOrderPlugin(),
            new webpack.optimize.DedupePlugin(),
            new webpack.optimize.UglifyJsPlugin({
                comments: false,
                compressor: {
                    drop_console: true // eslint-disable-line
                }
            })
        ]);
    }

    return baseConfig;
};

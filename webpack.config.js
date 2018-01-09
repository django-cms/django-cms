var webpack = require('webpack');
var path = require('path');
var Webpack2Polyfill = require('webpack2-polyfill-plugin');

module.exports = function(opts) {
    'use strict';

    var PROJECT_PATH = opts.PROJECT_PATH;
    var CMS_VERSION = opts.CMS_VERSION;
    var debug = opts.debug;

    if (!debug) {
        process.env.NODE_ENV = 'production';
    }

    var baseConfig = {
        devtool: false,
        watch: !!opts.watch,
        entry: {
            // CMS frontend
            toolbar: PROJECT_PATH.js + '/toolbar.js',
            // CMS admin
            'admin.base': PROJECT_PATH.js + '/admin.base.js',
            'admin.pagetree': PROJECT_PATH.js + '/admin.pagetree.js',
            'admin.changeform': PROJECT_PATH.js + '/admin.changeform.js',
            // CMS widgets
            // they will load the on-demand bundle called admin.widget
            'forms.pageselectwidget': PROJECT_PATH.js + '/widgets/forms.pageselectwidget.js',
            'forms.slugwidget': PROJECT_PATH.js + '/widgets/forms.slugwidget.js',
            'forms.pagesmartlinkwidget': PROJECT_PATH.js + '/widgets/forms.pagesmartlinkwidget.js',
            'forms.apphookselect': PROJECT_PATH.js + '/widgets/forms.apphookselect.js'
        },
        output: {
            path: PROJECT_PATH.js + '/dist/' + CMS_VERSION + '/',
            filename: 'bundle.[name].min.js',
            chunkFilename: 'bundle.[name].min.js',
            jsonpFunction: 'cmsWebpackJsonp'
        },
        plugins: [
            new Webpack2Polyfill(),
            // this way admin.pagetree bundle won't
            // include deps already required in admin.base bundle
            new webpack.optimize.CommonsChunkPlugin({
                name: 'admin.base',
                chunks: ['admin.pagetree', 'admin.changeform']
            })
        ],
        resolve: {
            alias: {
                jquery: PROJECT_PATH.js + '/libs/jquery.min.js',
                classjs: PROJECT_PATH.js + '/libs/class.min.js',
                jstree: PROJECT_PATH.js + '/libs/jstree/jstree.min.js'
            }
        },
        module: {
            rules: [
                // must be first
                {
                    test: /\.js$/,
                    use: [
                        {
                            loader: 'babel-loader',
                            options: {
                                retainLines: true
                            }
                        }
                    ],
                    exclude: /(node_modules|libs|addons\/jquery.*)/,
                    include: path.join(__dirname, 'cms')
                },
                {
                    test: /(modules\/jquery|libs\/pep|select2\/select2)/,
                    use: [
                        {
                            loader: 'imports-loader',
                            options: {
                                jQuery: 'jquery'
                            }
                        }
                    ]
                },
                {
                    test: /class.min.js/,
                    use: [
                        {
                            loader: 'exports-loader',
                            options: {
                                Class: true
                            }
                        }
                    ]
                },
                {
                    test: /.html$/,
                    use: [
                        {
                            loader: 'raw-loader'
                        }
                    ]
                }
            ]
        },
        stats: 'verbose'
    };

    if (debug) {
        baseConfig.devtool = 'cheap-module-eval-source-map';
        baseConfig.plugins = baseConfig.plugins.concat([
            new webpack.NoEmitOnErrorsPlugin(),
            new webpack.DefinePlugin({
                __DEV__: 'true',
                __CMS_VERSION__: JSON.stringify(CMS_VERSION)
            })
        ]);
    } else {
        baseConfig.plugins = baseConfig.plugins.concat([
            new webpack.DefinePlugin({
                __DEV__: 'false',
                __CMS_VERSION__: JSON.stringify(CMS_VERSION)
            }),
            new webpack.optimize.ModuleConcatenationPlugin(),
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

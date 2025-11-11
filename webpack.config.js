var webpack = require('webpack');
var path = require('path');
var TerserPlugin = require('terser-webpack-plugin');

module.exports = function(opts) {
    'use strict';

    var PROJECT_PATH = opts.PROJECT_PATH;
    var CMS_VERSION = opts.CMS_VERSION;
    var debug = opts.debug;

    if (!debug) {
        process.env.NODE_ENV = 'production';
    }

    var baseConfig = {
        mode: debug ? 'development' : 'production',
        target: ['web', 'es5'],
        devtool: false,
        watch: !!opts.watch,
        entry: {
            // CMS frontend
            toolbar: {
                import: PROJECT_PATH.js + '/toolbar.js',
                library: {
                    name: 'CMS',
                    type: 'window',
                    export: 'default'
                }
            },
            // CMS admin
            'admin.base': {
                import: PROJECT_PATH.js + '/admin.base.js',
                library: {
                    name: 'CMS',
                    type: 'window',
                    export: 'default'
                }
            },
            'admin.pagetree': {
                import: PROJECT_PATH.js + '/admin.pagetree.js',
                dependOn: 'admin.base'
            },
            'admin.changeform': {
                import: PROJECT_PATH.js + '/admin.changeform.js',
                library: {
                    name: 'CMS',
                    type: 'window',
                    export: 'default'
                }
            },
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
            publicPath: '/static/cms/js/dist/' + CMS_VERSION + '/',
            scriptType: 'text/javascript',
            globalObject: 'window'
        },
        optimization: {
            runtimeChunk: false,
            splitChunks: false,
            minimizer: []
        },
        plugins: [],
        resolve: {
            alias: {
                jquery: PROJECT_PATH.js + '/libs/jquery.min.js',
                classjs: PROJECT_PATH.js + '/libs/class.min.js',
                jstree: PROJECT_PATH.js + '/libs/jstree/jstree.min.js'
            },
            fallback: {
                path: false
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
                    test: /libs\/pep/,
                    use: [
                        {
                            loader: 'imports-loader',
                            options: {
                                wrapper: {
                                    thisArg: 'window',
                                    args: {
                                        module: false,
                                        exports: false
                                    }
                                }
                            }
                        }
                    ]
                },
                {
                    test: /(modules\/jquery|select2\/select2)/,
                    use: [
                        {
                            loader: 'imports-loader',
                            options: {
                                imports: {
                                    moduleName: 'jquery',
                                    name: 'jQuery'
                                }
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
                                type: 'commonjs',
                                exports: 'single Class'
                            }
                        }
                    ]
                },
                {
                    test: /.html$/,
                    type: 'asset/source'
                }
            ]
        },
        stats: 'verbose'
    };

    if (debug) {
        baseConfig.devtool = 'cheap-module-source-map';
        baseConfig.plugins = baseConfig.plugins.concat([
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
            })
        ]);
        baseConfig.optimization.minimizer.push(
            new TerserPlugin({
                terserOptions: {
                    compress: {
                        drop_console: true
                    },
                    format: {
                        comments: false
                    }
                },
                extractComments: false
            })
        );
    }

    return baseConfig;
};

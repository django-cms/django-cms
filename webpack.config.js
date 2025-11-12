var webpack = require('webpack');
var path = require('path');
var TerserPlugin = require('terser-webpack-plugin');
var LicenseWebpackPlugin = require('license-webpack-plugin').LicenseWebpackPlugin;

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
        plugins: [
            new LicenseWebpackPlugin({
                outputFilename: '../../../../../../LICENSE',
                perChunkOutput: false,
                addBanner: false,
                renderLicenses: (modules) => {
                    const copyright = `Copyright (c) 2008-present, Batiste Bieler
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above
      copyright notice, this list of conditions and the following
      disclaimer in the documentation and/or other materials provided
      with the distribution.
    * Neither the name of the author nor the names of other
      contributors may be used to endorse or promote products derived
      from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

This software bundles Javascript open source software using WebPack.
Please find their copyright notices here:

================================================================================

Package: class.min.js
Version: 1.0
Author: Angelo Dini
License: BSD License
Copyright: Distributed under the BSD License.

${'='.repeat(80)}

Package: jQuery
Version: 1.11.3
License: MIT License
Copyright: (c) 2005, 2015 jQuery Foundation, Inc.
License URL: jquery.org/license

${'='.repeat(80)}

Package: jsTree
Version: 3.3.0 (2016-04-25)
License: MIT License
License URL: https://github.com/vakata/jstree/blob/master/LICENSE-MIT
Copyright: (c) jsTree project
Note: THIS FILE HAS BEEN MANUALLY PATCHED TO ALLOW COPYING INTO SELF/CHILDREN
Source: https://github.com/FinalAngel/jstree

${'='.repeat(80)}

`;
                    const licenses = modules.map(module => {
                        const licenseText = module.licenseText || 'License text not found';
                        return `Package: ${module.packageJson.name || module.name}\nVersion: ${module.packageJson.version || 'N/A'}\nLicense: ${module.packageJson.license || 'N/A'}\n\n${licenseText}\n\n${'='.repeat(80)}\n`;
                    }).join('\n');
                    return copyright + licenses;
                }
            })
        ],
        resolve: {
            alias: {
                jquery: PROJECT_PATH.js + '/libs/jquery.min.js',
                classjs: PROJECT_PATH.js + '/libs/class.min.js',
                jstree: PROJECT_PATH.js + '/libs/jstree/jstree.min.js',
                // Use ES6 entry point for keyboardjs instead of UMD dist
                keyboardjs: 'keyboardjs/index.js'
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

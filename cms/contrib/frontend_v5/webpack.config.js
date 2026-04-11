/*
 * Webpack config for the frontend_v5 contrib app.
 *
 * DROP-IN REPLACEMENT CONTRACT
 * ----------------------------
 * The bundles emitted here MUST be drop-in replacements for the legacy
 * bundles built by /webpack.config.js. Concretely that means:
 *
 *   1. Same on-disk path inside the app: static/cms/js/dist/<CMS_VERSION>/
 *      So that when `cms.contrib.frontend_v5` is listed BEFORE `cms` in
 *      INSTALLED_APPS, Django staticfiles serves these files at the same
 *      URL as the legacy ones, with no template changes required. This is
 *      the standard Django app-ordering static-file override pattern.
 *
 *   2. Same bundle filenames as legacy:
 *        bundle.toolbar.min.js
 *        bundle.admin.base.min.js
 *        bundle.admin.pagetree.min.js
 *        bundle.admin.changeform.min.js
 *        bundle.forms.pageselectwidget.min.js
 *        bundle.forms.slugwidget.min.js
 *        bundle.forms.pagesmartlinkwidget.min.js
 *        bundle.forms.apphookselect.min.js
 *      Names MUST match exactly. Add new entries below as each module is
 *      ported (Step 3+ of the migration plan).
 *
 *   3. Same window-global API surface (window.CMS, CMS.$, CMS.API, etc.)
 *      enforced per-bundle via the `library` field on each entry, mirroring
 *      the legacy config.
 *
 * The hello / spike entries below are scaffolding artefacts that get
 * deleted once Step 1 is signed off — they do not need legacy parity.
 *
 * Independent of the legacy /webpack.config.js — both can run side by side.
 * Invoked from this app's gulpfile.
 */
const path = require('path');
const webpack = require('webpack');
const TerserPlugin = require('terser-webpack-plugin');

const APP_ROOT = __dirname;
const SRC = path.join(APP_ROOT, 'src');
// MUST mirror the legacy on-disk layout — see contract above.
const STATIC_OUT = path.join(APP_ROOT, 'static', 'cms', 'js', 'dist');

module.exports = function (opts) {
    'use strict';

    const debug = !!(opts && opts.debug);
    const CMS_VERSION = (opts && opts.CMS_VERSION) || 'dev';

    if (!debug) {
        process.env.NODE_ENV = 'production';
    }

    const config = {
        mode: debug ? 'development' : 'production',
        target: ['web', 'es2020'],
        devtool: debug ? 'cheap-module-source-map' : false,
        watch: !!(opts && opts.watch),
        entry: {
            // CMS widgets. Each entry here MUST match a legacy bundle
            // filename exactly — see the drop-in contract above.
            'forms.slugwidget': path.join(SRC, 'bundles', 'forms.slugwidget.ts'),
            'forms.pageselectwidget': path.join(SRC, 'bundles', 'forms.pageselectwidget.ts'),
            'forms.apphookselect': path.join(SRC, 'bundles', 'forms.apphookselect.ts'),
        },
        output: {
            path: path.join(STATIC_OUT, CMS_VERSION),
            filename: 'bundle.[name].min.js',
            chunkFilename: 'bundle.[name].min.js',
            publicPath: '/static/cms/js/dist/' + CMS_VERSION + '/',
            scriptType: 'text/javascript',
            globalObject: 'window',
            clean: true,
        },
        resolve: {
            extensions: ['.ts', '.js'],
            alias: {
                '@': SRC,
            },
        },
        module: {
            rules: [
                {
                    test: /\.ts$/,
                    include: SRC,
                    use: [
                        {
                            loader: 'babel-loader',
                            options: {
                                presets: [
                                    ['@babel/preset-env', { targets: { esmodules: true } }],
                                    '@babel/preset-typescript',
                                ],
                            },
                        },
                    ],
                },
            ],
        },
        plugins: [
            new webpack.DefinePlugin({
                __DEV__: JSON.stringify(debug),
                __CMS_VERSION__: JSON.stringify(CMS_VERSION),
            }),
        ],
        optimization: {
            runtimeChunk: false,
            splitChunks: false,
            minimizer: debug
                ? []
                : [
                      new TerserPlugin({
                          terserOptions: {
                              compress: { drop_console: true },
                              format: { comments: false },
                          },
                          extractComments: false,
                      }),
                  ],
        },
        stats: 'minimal',
    };

    return config;
};

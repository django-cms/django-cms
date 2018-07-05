const argv = require('minimist')(process.argv.slice(2));
const plugins = [];
const webpack = require('webpack');
const WebpackPolyfillPlugin = require('webpack2-polyfill-plugin');
const path = require('path');

// TODO check if polling is still required https://github.com/divio/djangocms-boilerplate-webpack/blob/master/webpack.config.debug.js#L16

process.env.NODE_ENV = argv.debug ? 'development' : 'production';

plugins.push(new WebpackPolyfillPlugin());

// Bundle splitting. Don't forget to {% addtoblock "js" %} afterwards
plugins.push(
    new webpack.optimize.CommonsChunkPlugin({
        name: 'base',
        chunks: ['base', 'cms', 'press'],
    }),
    new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
);

// add plugins depending on if we are debugging or not
if (argv.debug) {
    plugins.push(
        new webpack.LoaderOptionsPlugin({
            minimize: false,
            debug: true,
        })
    );
    plugins.push(
        new webpack.DefinePlugin({
            DEBUG: 'true',
        })
    );
} else {
    plugins.push(new webpack.optimize.ModuleConcatenationPlugin());
    plugins.push(new webpack.optimize.OccurrenceOrderPlugin());
    plugins.push(
        new webpack.LoaderOptionsPlugin({
            minimize: true,
            debug: false,
        })
    );
    plugins.push(
        new webpack.DefinePlugin({
            DEBUG: 'false',
        })
    );
    plugins.push(
        new webpack.optimize.UglifyJsPlugin({
            beautify: false,
            mangle: {
                screw_ie8: true,
                keep_fnames: true,
            },
            compress: {
                screw_ie8: true,
            },
            comments: false,
        })
    );
}

module.exports = {
    devtool: argv.debug ? 'cheap-module-eval-source-map' : false,
    entry: {
        base: path.join(__dirname, 'base.js'),
        cms: path.join(__dirname, 'cms.js'),
        press: path.join(__dirname, 'press.js'),
        // detail: path.join(__dirname, 'detail.js'),
    },
    output: {
        path: path.join(__dirname, '..', '..', 'static', 'js', 'dist'),
        filename: '[name].bundle.js',
        publicPath: '/static/',
    },
    plugins: plugins,
    resolve: {
        modules: [__dirname, 'node_modules'],
        alias: {
            // make sure that we always use our jquery when loading 3rd party plugins
            jquery: require.resolve('jquery'),
            outdatedbrowser: path.join(__dirname, 'libs', 'outdatedBrowser.min.js'),
        },
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                use: [
                    {
                        loader: 'babel-loader',
                        options: {
                            retainLines: true,
                        },
                    },
                ],
                exclude: /(node_modules|vendor|libs|addons\/jquery.*)/,
                include: __dirname,
            },
            {
                test: /outdatedBrowser/,
                use: [
                    {
                        loader: 'exports-loader',
                        options: {
                            outdatedBrowser: true,
                        },
                    },
                ],
            },
            {
                test: /bootstrap(?!-breakpoints)/,
                use: [
                    {
                        loader: 'imports-loader',
                        options: {
                            $: 'jquery',
                            'window.jQuery': 'jquery',
                            jQuery: 'jquery',
                            PopperModule: 'popper.js',
                            Popper: '>PopperModule.default',
                        },
                    },
                ],
            },
        ],
    },
};

// disable DeprecationWarning: loaderUtils.parseQuery() DeprecationWarning
process.noDeprecation = true;

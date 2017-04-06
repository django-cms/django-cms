const argv = require('minimist')(process.argv.slice(2));
const plugins = [];
const webpack = require('webpack');


// TODO check if polling is still required https://github.com/divio/djangocms-boilerplate-webpack/blob/master/webpack.config.debug.js#L16
// TODO check plugin usage
// TODO path concatination should be path.join

process.env.NODE_ENV = (argv.debug) ? 'development' : 'production';

// add plugins depending on if we are debugging or not
if (argv.debug) {
    plugins.push(
        new webpack.LoaderOptionsPlugin({
            minimize: false,
            debug: true,
        })
    );
} else {
    plugins.push(new webpack.optimize.OccurrenceOrderPlugin());
    plugins.push(
        new webpack.LoaderOptionsPlugin({
            minimize: true,
            debug: false,
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
    devtool: argv.debug ? 'eval' : false,
    entry: {
        base: __dirname + '/base.js',
    },
    output: {
        path: __dirname + '/../../static/js/',
        filename: '[name].bundle.js',
        publicPath: '/static/',
    },
    plugins: plugins,
    resolve: {
        modules: [__dirname, 'node_modules'],
        alias: {
            // make sure that we always use our jquery when loading 3rd party plugins
            jquery: require.resolve('jquery'),
            outdatedbrowser: __dirname + '/libs/outdatedBrowser.min.js',
        },
    },
    module: {
        rules: [
            {
                test: /\.js$/,
                use: [{
                    loader: 'babel-loader',
                }],
                exclude: /(node_modules|vendor|libs|addons\/jquery.*)/,
                include: __dirname,
            },
            {
                test: /outdatedBrowser/,
                use: [{
                    loader: 'exports-loader',
                    options: {
                        outdatedBrowser: true,
                    },
                }],

            },
            {
                test: /bootstrap-sass/,
                use: [{
                    loader: 'imports-loader',
                    options: {
                        jQuery: 'jquery',
                    },
                }],
            },
        ],
    },
}

// disable DeprecationWarning: loaderUtils.parseQuery() DeprecationWarning
process.noDeprecation = true

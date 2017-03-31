const argv = require('minimist')(process.argv.slice(2));
const plugins = [];
const webpack = require('webpack');


// add plugins depending on if we are debugging or not
if (argv.debug) {
    plugins.push(
        new webpack.LoaderOptionsPlugin({
            minimize: false,
            debug: true
        })
    );
} else {
    plugins.push(new webpack.optimize.OccurrenceOrderPlugin());
    plugins.push(
        new webpack.LoaderOptionsPlugin({
            minimize: true,
            debug: false
        })
    );
    plugins.push(
        new webpack.optimize.UglifyJsPlugin({
            beautify: false,
            mangle: {
                screw_ie8: true,
                keep_fnames: true
            },
            compress: {
                screw_ie8: true
            },
            comments: false
        })
    );
}

module.exports = {
    devtool: argv.debug ? 'eval' : false,
    entry: [
        __dirname + '/base.js'
    ],
    output: {
        path: __dirname + '/../../static/js/',
        filename: 'base.bundle.js',
        publicPath: '/',
        sourceMapFilename: 'base.map'
    },
    plugins: plugins,
    module: {
        loaders: [
            // registers babel transpiler
            {
                loader: 'babel-loader',
                test: /\.js$/,
                exclude: /(node_modules|vendor|libs|addons\/jquery.*|tests\/unit\/helpers)/,
                include: __dirname,
                query: {
                    plugins: ['transform-runtime'],
                    presets: ['es2015', 'es2017'],
                }
            }
        ]
    }
}

// disable DeprecationWarning: loaderUtils.parseQuery() DeprecationWarning
process.noDeprecation = true

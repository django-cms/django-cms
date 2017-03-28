process.env.NODE_ENV = 'production';

var webpack = require('webpack');
var base = require('./webpack.config.base');
var _ = require('lodash');

var config = _.merge(base, {
    devtool: false,
    plugins: [
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
    ]
});

module.exports = config;

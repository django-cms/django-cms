var webpack = require('webpack');
var base = require('./webpack.config.base');
var _ = require('lodash');

var config = _.merge(base, {
    devtool: 'eval',
    plugins: [
        new webpack.DefinePlugin({
            __DEV__: 'true'
        })
    ]
});

// in case we are running inside Docker container on Aldryn
// we need to resort to polling
if (process.env.GULP_MODE === 'production') {
    config.watchOptions = {
        poll: 300
    };
}

module.exports = config;

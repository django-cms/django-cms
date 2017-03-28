var webpack = require('webpack');

module.exports = {
    devtool: false,
    entry: [
        './static/js/base'
    ],
    output: {
        path: __dirname + '/static/js/dist/',
        filename: 'bundle.js',
        publicPath: '/'
    },
    plugins: [
        new webpack.NoErrorsPlugin(),
        new webpack.DefinePlugin({
            __DEV__: 'true'
        })
    ],
    resolve: {
        extensions: ['', '.js'],
        alias: {
            jquery: require.resolve('jquery'),
            outdatedbrowser: __dirname + '/static/js/libs/outdatedBrowser.min.js'
        }
    },
    module: {
        loaders: [
            {
                test: /\.js$/,
                loader: 'babel',
                exclude: /(node_modules|vendor|libs|tests\/unit\/helpers)/,
                include: __dirname
            },
            {
                test: /outdatedBrowser/,
                loader: 'exports?outdatedBrowser'
            },
            {
                test: /swfobject/,
                loaders: [
                    'exports?swfobject'
                ]
            },
            {
                test: /bootstrap-sass/,
                loaders: [
                    'imports?jQuery=jquery'
                ]
            }
        ]
    }
};

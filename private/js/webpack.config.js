const argv = require('minimist')(process.argv.slice(2));


module.exports = {
    devtool: argv.DEBUG ? 'eval' : false,
    entry: [
        __dirname + '/base.js'
    ],
    output: {
        path: __dirname + '/../../static/js/',
        filename: 'base.bundle.js',
        publicPath: '/'
    },
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

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
    }
}

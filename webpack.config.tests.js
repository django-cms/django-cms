// this config is used for integration tests only

module.exports = {
    entry: './tests/integration/index',
    output: {
        filename: 'index.bundle.js',
        path: './tests/integration/'
    },
    module: {
        loaders: [{
            test: /\.js$/,
            loader: 'babel',
            exclude: /(node_modules|vendor|libs|tests\/unit\/helpers)/,
            include: __dirname
        }]
    }
};

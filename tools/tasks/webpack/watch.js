var gutil = require('gulp-util');
var webpack = require('webpack');

module.exports = function () {
    return function () {
        var config = require('../../../webpack.config.debug');

        config.watch = true;
        // run webpack
        webpack(config, function (err, stats) {
            if (err) {
                throw new gutil.PluginError('webpack', err);
            }
            gutil.log('[webpack]', stats.toString({ colors: true }));
        });
    };
};

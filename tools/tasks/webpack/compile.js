const gutil = require('gulp-util');
const webpack = require('webpack');


module.exports = function (gulp, opts) {
    return function (callback) {
        var config = require(opts.PROJECT_PATH.webpack + '/webpack.config');

        webpack(config, function (err, stats) {
            if (err) {
                throw new gutil.PluginError('webpack', err);
            }
            gutil.log('[webpack]', stats.toString({ colors: true }));
            callback();
        });
    };
};

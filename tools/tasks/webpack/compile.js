const gutil = require('gulp-util');
const webpack = require('webpack');

module.exports = function(gulp, opts) {
    return function(callback) {
        var config = require(opts.PROJECT_PATH.webpack + '/webpack.config');

        config.watch = opts.watch;

        webpack(config, function(err, stats) {
            if (err) {
                throw new gutil.PluginError('webpack', err);
            }
            gutil.log(
                '[webpack]',
                stats.toString({
                    colors: true,
                    maxModules: Infinity,
                    optimizationBailout: true,
                })
            );
            if (!opts.watch) {
                callback();
            }
        });
    };
};

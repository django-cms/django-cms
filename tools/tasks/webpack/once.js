var gutil = require('gulp-util');
var webpack = require('webpack');

module.exports = function (gulp, opts) {
    return function (callback) {
        var config = opts.DEBUG ? 'webpack.config.debug' : 'webpack.config.production';

        gutil.log('[BUILD] Webpack using config: ' + config);

        // run webpack
        webpack(require('../../../' + config), function (err, stats) {
            if (err) {
                throw new gutil.PluginError('webpack', err);
            }
            gutil.log('[webpack]', stats.toString({ colors: true }));
            callback();
        });
    };
};

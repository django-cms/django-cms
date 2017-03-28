var browserSync = require('browser-sync');

module.exports = function (gulp, opts) {
    return function () {
        var files = [
            opts.PROJECT_PATH.css + '/*.css',
            opts.PROJECT_PATH.html + '/**/*.html',
            opts.PROJECT_PATH.js + '/**/*.js'
        ];
        var syncTimeout = 1000;

        // DOCS: http://www.browsersync.io/docs/options/
        setTimeout(function () {
            browserSync.init(files, {
                proxy: '0.0.0.0:' + opts.PORT,
                port: opts.PORT + 1,
                ui: {
                    port: opts.PORT + 2
                }
            });
        }, syncTimeout);
    };
};

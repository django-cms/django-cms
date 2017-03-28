var gutil = require('gulp-util');
var cache = require('gulp-cached');
var imagemin = require('gulp-imagemin');

module.exports = function (gulp, opts) {
    return function () {
        var options = {
            interlaced: true,
            optimizationLevel: 5,
            progressive: true
        };

        gulp.src(opts.PROJECT_PATTERNS.images)
            .pipe(cache(imagemin(options)))
            .pipe(gulp.dest(opts.PROJECT_PATH.images)).on('error', function (error) {
                gutil.log('\n' + error.message);
            });
    };
};

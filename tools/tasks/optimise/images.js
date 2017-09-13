const gutil = require('gulp-util');
const imagemin = require('gulp-imagemin');


module.exports = function (gulp, opts) {
    return function () {
        const options = {
            interlaced: true,
            optimizationLevel: 5,
            progressive: true,
        };

        return gulp.src(opts.PROJECT_PATTERNS.images)
            .pipe(imagemin(options))
            .on('error', function (error) {
                gutil.log(gutil.colors.red(
                    'Error (' + error.plugin + '): ' + error.messageFormatted)
                );
            })
            .pipe(gulp.dest(opts.PROJECT_PATH.images));
    };
};

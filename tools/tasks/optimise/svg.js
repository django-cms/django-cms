const gutil = require('gulp-util');
const imagemin = require('gulp-imagemin');


module.exports = function (gulp, opts) {
    return function () {
        return gulp.src(opts.PROJECT_PATTERNS.svg)
            .pipe(imagemin([
                imagemin.svgo({
                    plugins: [{
                        removeDimensions: true,
                    }],
                })],
                // options
                {
                    verbose: true,
                }
            ))
            .on('error', function (error) {
                gutil.log(gutil.colors.red(
                    'Error (' + error.plugin + '): ' + error.messageFormatted)
                );
            })
            .pipe(gulp.dest(opts.PROJECT_PATH.svg));
    };
};

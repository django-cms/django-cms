var eslint = require('gulp-eslint');
var plumber = require('gulp-plumber');
var gulpif = require('gulp-if');

module.exports = function (gulp, opts) {
    return function () {
        // DOCS: http://eslint.org/docs/user-guide/
        return gulp.src(opts.PROJECT_PATTERNS.js)
            .pipe(gulpif(!process.env.CI, plumber()))
            .pipe(eslint())
            .pipe(eslint.format())
            .pipe(eslint.failAfterError())
            .pipe(gulpif(!process.env.CI, plumber.stop()));
    };
};

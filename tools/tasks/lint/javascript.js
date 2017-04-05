const eslint = require('gulp-eslint');


module.exports = function (gulp, opts) {
    return function () {
        return gulp.src(opts.PROJECT_PATTERNS.js)
            .pipe(eslint({
                configFile: opts.PROJECT_PATH.webpack + '/.eslintrc.js'
            }))
            .pipe(eslint.format())
            .pipe(eslint.failAfterError());
    };
};

var bower = require('gulp-bower');

module.exports = function (gulp, opts) {
    return function () {
        return bower(gulp.dest(opts.PROJECT_PATH.bower));
    };
};

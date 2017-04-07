const checkFileSize = require('gulp-check-filesize');


module.exports = function (gulp, opts) {
    return function () {
        return gulp.src(opts.PROJECT_PATH.css + '/*-critical.css')
            .pipe(checkFileSize({
                fileSizeLimit: '14336',
            }));
            // TODO add inline script, prevent if debug param is passed
            // write to includes/critical_css.html
    };
};

const checkFileSize = require('gulp-check-filesize');
const cleanCSS = require('gulp-clean-css');
const concat = require('gulp-concat-util');
const rename = require('gulp-rename')


module.exports = function (gulp, opts) {
    return function () {
        return gulp.src(opts.PROJECT_PATH.css + '/*-critical.css')
            .pipe(checkFileSize({
                fileSizeLimit: '14336',
            }))
            // inline the file into the correct location
            // written into templates/includes/critical_css.html
            .pipe(cleanCSS())
            .pipe(concat.header('<style>'))
            .pipe(concat.footer('</style>'))
            .pipe(rename({
                basename: 'critical_css',
                extname: '.html',
            }))
            .pipe(gulp.dest(opts.PROJECT_PATH.html + '/includes'));
    };
};

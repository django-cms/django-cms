const cleanCSS = require('gulp-clean-css');
const concat = require('gulp-concat-util');
const criticalSplit = require('postcss-critical-split');
const gulpif = require('gulp-if');
const postcss = require('gulp-postcss');
const rename = require('gulp-rename')
const sourcemaps = require('gulp-sourcemaps');


module.exports = function (gulp, opts) {
    return function () {
        return gulp.src(opts.PROJECT_PATTERNS.css)
            .pipe(gulpif(opts.argv.debug, sourcemaps.init({ 'loadMaps': true })))
            .pipe(
                postcss([
                    criticalSplit({
                        output: 'critical',
                    }),
                ])
            )
            .pipe(gulpif(!opts.argv.debug, cleanCSS({
                rebase: false,
            })))
            .pipe(rename({
                suffix: '-critical',
            }))
            .pipe(concat.header(
                '/*\n    This file is generated.\n' +
                '    Do not edit directly.\n' +
                '    Edit original files in\n' +
                '    /private/sass instead\n */ \n\n'
            ))
            .pipe(gulpif(opts.argv.debug, sourcemaps.write()))
            .pipe(gulp.dest(opts.PROJECT_PATH.css));
    };
};

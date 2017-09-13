const cleanCSS = require('gulp-clean-css');
const concat = require('gulp-concat-util');
const criticalSplit = require('postcss-critical-split');
const gulpif = require('gulp-if');
const postcss = require('gulp-postcss');
const sourcemaps = require('gulp-sourcemaps');


module.exports = function (gulp, opts) {
    return function () {
        // generate sass, optionally with sourcemaps and without cleaned css
        return gulp.src(opts.PROJECT_PATTERNS.css)
            .pipe(gulpif(opts.argv.debug, sourcemaps.init({ 'loadMaps': true })))
            .pipe(
                postcss([
                    criticalSplit({
                        output: 'rest',
                    }),
                ])
            )
            .pipe(gulpif(!opts.argv.debug, cleanCSS({
                rebase: false,
            })))
            // this information is added on top of the generated .css file
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

const autoprefixer = require('autoprefixer');
const gulpif = require('gulp-if');
const gutil = require('gulp-util');
const postcss = require('gulp-postcss');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
const cleanCSS = require('gulp-clean-css');
const concat = require('gulp-concat-util');
const { importer } = require('npm-sass');

module.exports = function(gulp, opts) {
    return function() {
        return gulp
            .src(opts.PROJECT_PATTERNS.sass)
            .pipe(gulpif(opts.argv.debug, sourcemaps.init()))
            .pipe(sass({
                importer: importer,
                precision: 10,
            }))
            .on('error', function(error) {
                gutil.log(gutil.colors.red('Error (' + error.plugin + '): ' + error.messageFormatted));

                // used on Divio Cloud to inform divio app about the errors in
                // SASS compilation
                if (process.env.EXIT_ON_ERRORS) {
                    process.exit(1); // eslint-disable-line
                } else {
                    // in dev mode - just continue
                    this.emit('end');
                }
            })
            .pipe(
                postcss([
                    autoprefixer({
                        // browsers are coming from browserslist file
                        cascade: false,
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

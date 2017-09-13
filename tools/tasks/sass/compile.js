const autoprefixer = require('autoprefixer');
const gulpif = require('gulp-if');
const gutil = require('gulp-util');
const postcss = require('gulp-postcss');
const sass = require('gulp-sass');
const sourcemaps = require('gulp-sourcemaps');
// https://gist.github.com/chriseppstein/d7be56e21b216275bd86
// Eyeglass is used to auto-discover bootstrap from npm.
// Version 0.7 is required as bootstrap-sass pinns it in their package.json.
const Eyeglass = require('eyeglass').Eyeglass;
const eyeglass = new Eyeglass({
    importer: function(uri, prev, done) {
        done(sass.compiler.types.NULL);
    },
    // important to have no rounding errors
    precision: 10,
});

module.exports = function(gulp, opts) {
    return function() {
        return gulp
            .src(opts.PROJECT_PATTERNS.sass)
            .pipe(gulpif(opts.argv.debug, sourcemaps.init()))
            .pipe(sass(eyeglass.sassOptions()))
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
            .pipe(gulpif(opts.argv.debug, sourcemaps.write()))
            .pipe(gulp.dest(opts.PROJECT_PATH.css));
    };
};

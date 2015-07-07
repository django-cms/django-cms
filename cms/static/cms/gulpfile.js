'use strict';

// #####################################################################################################################
// #IMPORTS#
var autoprefixer = require('gulp-autoprefixer');
var gulp = require('gulp');
var gutil = require('gulp-util');
var gulpif = require('gulp-if');
var iconfont = require('gulp-iconfont');
var iconfontCss = require('gulp-iconfont-css');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var minifyCss = require('gulp-minify-css');
var jshint = require('gulp-jshint');
var jscs = require('gulp-jscs');

var argv = require('minimist')(process.argv.slice(2));

// #####################################################################################################################
// #SETTINGS#
var options = {
    debug: argv.debug
};
var PROJECT_ROOT = __dirname;
var PROJECT_PATH = {
    js: PROJECT_ROOT + '/js',
    sass: PROJECT_ROOT + '/sass',
    css: PROJECT_ROOT + '/css',
    icons: PROJECT_ROOT + '/fonts'
};

var PROJECT_PATTERNS = {
    js: [
        PROJECT_PATH.js + '/modules/*.js',
        '!' + PROJECT_PATH.js + '/modules/jquery.ui.*.js',
        '/gulpfile.js',
    ],
    sass: [
        PROJECT_PATH.sass + '/**/*.{scss,sass}'
    ],
    icons: [
        PROJECT_PATH.icons + '/src/*.svg'
    ]
};

// #####################################################################################################################
// #TASKS#
gulp.task('sass', function () {
    gulp.src(PROJECT_PATTERNS.sass)
        .pipe(gulpif(options.debug, sourcemaps.init()))
        .pipe(sass())
        .on('error', function (error) {
            gutil.log(gutil.colors.red('Error (' + error.plugin + '): ' + error.messageFormatted));
        })
        .pipe(autoprefixer({
            browsers: ['last 3 versions'],
            cascade: false
        }))
        .pipe(minifyCss())
        .pipe(gulpif(options.debug, sourcemaps.write()))
        .pipe(gulp.dest(PROJECT_PATH.css));
});

gulp.task('icons', function () {
    gulp.src(PROJECT_PATTERNS.icons)
    .pipe(iconfontCss({
        fontName: 'django-cms-iconfont',
        fontPath: '../fonts/',
        path: PROJECT_PATH.sass + '/libs/_iconfont.scss',
        targetPath: '../sass/components/_iconography.scss'
    }))
    .pipe(iconfont({
        fontName: 'django-cms-iconfont',
        normalize: true
    }))
    .on('glyphs', function(glyphs, options) {
        gutil.log.bind(glyphs, options);
    })
    .pipe(gulp.dest(PROJECT_PATH.icons));
});

gulp.task('lint', ['lint:javascript']);
gulp.task('lint:javascript', function () {
    // DOCS: http://jshint.com/docs/
    return gulp.src(PROJECT_PATTERNS.js)
        .pipe(jshint())
        .pipe(jscs())
        .on('error', function (error) {
            gutil.log('\n' + error.message);
            if (process.env.CI) {
                // Force the process to exit with error code
                process.exit(1);
            }
        })
        .pipe(jshint.reporter('jshint-stylish'));
});

gulp.task('watch', function () {
    gulp.watch(PROJECT_PATTERNS.sass, ['sass']);
    gulp.watch(PROJECT_PATTERNS.js, ['lint']);
});

gulp.task('default', ['sass', 'lint', 'watch']);

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
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');

var argv = require('minimist')(process.argv.slice(2));

// #####################################################################################################################
// #SETTINGS#
var options = {
    debug: argv.debug
};
var PROJECT_ROOT = __dirname + '/cms/static/cms';
var PROJECT_PATH = {
    js: PROJECT_ROOT + '/js',
    sass: PROJECT_ROOT + '/sass',
    css: PROJECT_ROOT + '/css',
    icons: PROJECT_ROOT + '/fonts'
};

var PROJECT_PATTERNS = {
    js: [
        PROJECT_PATH.js + '/modules/*.js',
        PROJECT_PATH.js + '/gulpfile.js',
        '!' + PROJECT_PATH.js + '/modules/jquery.ui.*.js',
        '!' + PROJECT_PATH.js + '/dist/*.js'
    ],
    sass: [
        PROJECT_PATH.sass + '/**/*.{scss,sass}'
    ],
    icons: [
        PROJECT_PATH.icons + '/src/*.svg'
    ]
};

/*
 * Object keys are filenames of bundles that will be compiled
 * from array of paths that are the value.
 */
var JS_BUNDLES = {
    'bundle.jstree.min.js': [
        PROJECT_PATH.js + '/jstree/_lib/_all.js',
        PROJECT_PATH.js + '/jstree/tree_component.js'
    ],
    'bundle.admin.base.min.js': [
        PROJECT_PATH.js + '/libs/jquery.min.js',
        PROJECT_PATH.js + '/libs/class.min.js',
        PROJECT_PATH.js + '/modules/cms.base.js'
    ],
    'bundle.toolbar.min.js': [
        PROJECT_PATH.js + '/libs/jquery.min.js',
        PROJECT_PATH.js + '/libs/class.min.js',
        PROJECT_PATH.js + '/modules/jquery.ui.custom.js',
        PROJECT_PATH.js + '/modules/jquery.ui.nestedsortable.js',
        PROJECT_PATH.js + '/modules/cms.base.js',
        PROJECT_PATH.js + '/modules/cms.modal.js',
        PROJECT_PATH.js + '/modules/cms.sideframe.js',
        PROJECT_PATH.js + '/modules/cms.clipboard.js',
        PROJECT_PATH.js + '/modules/cms.plugins.js',
        PROJECT_PATH.js + '/modules/cms.structureboard.js',
        PROJECT_PATH.js + '/modules/cms.toolbar.js'
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
    .on('glyphs', function (glyphs, options) {
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

Object.keys(JS_BUNDLES).forEach(function (bundleName) {
    var bundleFiles = JS_BUNDLES[bundleName];

    gulp.task('bundle:' + bundleName, function () {
        return gulp.src(bundleFiles)
            .pipe(gulpif(options.debug, sourcemaps.init()))
            .pipe(uglify({
                preserveComments: 'some'
            }))
            .pipe(concat(bundleName, {
                newLine: '\n'
            }))
            .pipe(gulpif(options.debug, sourcemaps.write()))
            .pipe(gulp.dest(PROJECT_PATH.js + '/dist/'));
    });
});
gulp.task('bundle', Object.keys(JS_BUNDLES).map(function (bundleName) {
    return 'bundle:' + bundleName;
}));

gulp.task('watch', function () {
    gulp.watch(PROJECT_PATTERNS.sass, ['sass']);
    gulp.watch(PROJECT_PATTERNS.js, ['lint']);
    Object.keys(JS_BUNDLES).forEach(function (bundleName) {
        var bundleFiles = JS_BUNDLES[bundleName];
        gulp.watch(bundleFiles, ['bundle:' + bundleName]);
    });
});

gulp.task('default', ['sass', 'lint', 'bundle', 'watch']);

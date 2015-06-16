'use strict';

// #####################################################################################################################
// #IMPORTS#
var autoprefixer = require('gulp-autoprefixer');
var gulp = require('gulp');
var gutil = require('gulp-util');
var iconfont = require('gulp-iconfont');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var minifyCss = require('gulp-minify-css');

// #####################################################################################################################
// #SETTINGS#
var PROJECT_ROOT = '.';
var PROJECT_PATH = {
    'sass': PROJECT_ROOT + '/sass',
    'css': PROJECT_ROOT + '/css',
    'icons': PROJECT_ROOT + '/fonts'
};

var PROJECT_PATTERNS = {
    'sass': [
        PROJECT_PATH.sass + '/**/*.{scss,sass}'
    ],
    'icons': [
        PROJECT_PATH.icons + '/src/*.svg'
    ]
};

// #####################################################################################################################
// #TASKS#
gulp.task('sass', function () {
    gulp.src(PROJECT_PATTERNS.sass)
        .pipe(sourcemaps.init())
        .pipe(sass())
        .on('error', gutil.log.bind(console))
        .pipe(autoprefixer({
            browsers: ['last 3 versions'],
            cascade: false
        }))
        .pipe(minifyCss())
        .pipe(sourcemaps.write())
        .pipe(gulp.dest(PROJECT_PATH.css));
});

gulp.task('icons', function () {
    gulp.src(PROJECT_PATTERNS.icons)
    .pipe(iconfont({
        fontName: 'django-cms-icons',
        startUnicode: true
    }))
    .on('glyphs', function(glyphs, options) {
        gutil.log.bind(glyphs, options);
    })
    .pipe(gulp.dest(PROJECT_PATH.icons));
});

gulp.task('watch', function () {
    gulp.watch(PROJECT_PATTERNS.sass, ['sass']);
});

gulp.task('default', ['sass', 'watch']);

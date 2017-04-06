/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * http://github.com/divio/djangocms-boilerplate-webpack
 */

// TODO:
// - The minimatch/graceful-fs warnings are from gulp, needs upgrade to 4.0 once released.

// #############################################################################
// IMPORTS
const argv = require('minimist')(process.argv.slice(2));
const gulp = require('gulp');

// #############################################################################
// SETTINGS
const PROJECT_ROOT = __dirname;
const PROJECT_PATH = {
    css: PROJECT_ROOT + '/static/css',
    // images: PROJECT_ROOT + '/static/img',
    sass: PROJECT_ROOT + '/private/sass',
    sprites: PROJECT_ROOT + '/static/sprites',
    svg: PROJECT_ROOT + '/private/svg',
    js: PROJECT_ROOT + '/static/js',
    webpack: PROJECT_ROOT + '/private/js',
};
const PROJECT_PATTERNS = {
    // images: [
    //     PROJECT_PATH.images + '/**/*',
    //     // exclude from preprocessing
    //     '!' + PROJECT_PATH.images + '/dummy/*/**'
    // ],
    svg: [
        PROJECT_PATH.svg + '/**/*.svg',
    ],
    js: [
        '*.js',
        './tools/tasks/**/*.js',
        PROJECT_PATH.webpack + '*.config.js',
        PROJECT_PATH.webpack + '/**/*.js',
        '!' + PROJECT_PATH.webpack + '/*.min.js',
        '!' + PROJECT_PATH.webpack + '/**/*.min.js',
    ],
    css: [
        PROJECT_PATH.css + '/*base*.css',
        '!' + PROJECT_PATH.css + '/*-critical.css',
    ],
    sass: [
        PROJECT_PATH.sass + '/**/*.{scss,sass}',
        '!' + PROJECT_PATH.sass + '/libs/_svgsprite.scss',
    ],
};
//
// var DEFAULT_PORT = 8000;
// var PORT = parseInt(process.env.PORT, 10) || DEFAULT_PORT;

// #############################################################################
// TASKS

/**
 * Checks project deployment
 * @param {String} id - task name
 * @returns {Object} - task which finished
 */
function task(id) {
    return require('./tools/tasks/' + id)(gulp, {
        PROJECT_ROOT: PROJECT_ROOT,
        PROJECT_PATH: PROJECT_PATH,
        PROJECT_PATTERNS: PROJECT_PATTERNS,
        argv: argv,
    });
}

/**
 * Usage:
 * - "gulp sass" (generates sass, splits the files, and injects the code)
 * - "gulp sass --debug" (to generate unminified css with sourcemaps)
 * - "gulp sass:compile" (just generates the base.css out of sass, handy to skip critical css)
 * - "gulp sass:critical" (splits the base.css with the critical css)
 * - "gulp sass:rest" (splits the base.css with the remaining "rest" css)
 * - "gulp sass:inline" (injects the base-critical.css as inline css into the template)
 */
gulp.task('sass', ['sass:critical', 'sass:rest', 'sass:inline']);
gulp.task('sass:compile', task('sass/compile'));
gulp.task('sass:critical', ['sass:compile'], task('sass/critical'));
gulp.task('sass:rest', ['sass:compile'], task('sass/rest'));
gulp.task('sass:inline', ['sass:critical'], task('sass/inline'));

/**
 * Usage:
 * - "gulp lint" (runs sass and js linter)
 * - "gulp lint --debug" (switches linters to verbose mode)
 * - "gulp lint:sass" (runs the linter for sass)
 * - "gulp lint:javascript" (runs the linter for javascript)
 */
gulp.task('lint', ['lint:sass', 'lint:javascript']);
gulp.task('lint:sass', task('lint/sass'));
gulp.task('lint:javascript', task('lint/javascript'));

/**
 * Usage:
 * - "gulp webpack" (compiles javascript)
 * - "gulp webpack --debug" (disables compressions and adds sourcemaps)
 * - "gulp webpack --watch" (separately watch js instead of gulp watch)
 * - "gulp webpack:compile" (compiles javascript)
 */
gulp.task('webpack', ['webpack:compile']);
gulp.task('webpack:compile', task('webpack/compile'));

/**
 * Usage:
 * - "gulp icons" (compiles to sprites and sass)
 */
gulp.task('icons', task('icons/svgsprite'));

/**
 * Usage:
 * - "gulp optimise" (runs various optimisation tools)
 * - "gulp optimise:svg" (ensures svg files are minified and optimised)
 */
gulp.task('optimise', ['optimise:svg']);
gulp.task('optimise:svg', task('optimise/svg'));

/**
 * process.env.GULP_MODE === 'production' means we have a limited
 * subset of tasks to speed up the deployment / installation process.
 */
gulp.task('default', ['sass', 'webpack', 'lint']);
gulp.task('watch', function () {
    gulp.watch(PROJECT_PATTERNS.sass, ['sass', 'lint:sass']);
    gulp.watch(PROJECT_PATTERNS.js, ['webpack', 'lint:javascript']);
});
// used on the cloud
gulp.task('build', ['sass', 'webpack']);

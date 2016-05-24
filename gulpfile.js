/* eslint strict: [2, "global"] */
'use strict';

// #####################################################################################################################
// #IMPORTS#
var gulp = require('gulp');
var gutil = require('gulp-util');
var fs = require('fs');
var autoprefixer = require('autoprefixer');
var postcss = require('gulp-postcss');
var gulpif = require('gulp-if');
var iconfont = require('gulp-iconfont');
var iconfontCss = require('gulp-iconfont-css');
var sass = require('gulp-sass');
var sourcemaps = require('gulp-sourcemaps');
var minifyCss = require('gulp-clean-css');
var eslint = require('gulp-eslint');
var concat = require('gulp-concat');
var uglify = require('gulp-uglify');
var KarmaServer = require('karma').Server;
var integrationTests = require('djangocms-casper-helpers/gulp');

var argv = require('minimist')(process.argv.slice(2)); // eslint-disable-line

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
    icons: PROJECT_ROOT + '/fonts',
    tests: __dirname + '/cms/tests/frontend'
};

var PROJECT_PATTERNS = {
    js: [
        PROJECT_PATH.js + '/modules/*.js',
        PROJECT_PATH.js + '/widgets/*.js',
        PROJECT_PATH.js + '/gulpfile.js',
        PROJECT_PATH.tests + '/**/*.js',
        '!' + PROJECT_PATH.tests + '/unit/helpers/**/*.js',
        '!' + PROJECT_PATH.tests + '/coverage/**/*.js',
        '!' + PROJECT_PATH.js + '/modules/jquery.*.js',
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
    'bundle.admin.base.min.js': [
        PROJECT_PATH.js + '/polyfills/function.prototype.bind.js',
        PROJECT_PATH.js + '/libs/jquery.min.js',
        PROJECT_PATH.js + '/libs/pep.js',
        PROJECT_PATH.js + '/libs/class.min.js',
        PROJECT_PATH.js + '/modules/cms.base.js'
    ],
    'bundle.admin.changeform.min.js': [
        PROJECT_PATH.js + '/modules/cms.changeform.js'
    ],
    'bundle.admin.pagetree.min.js': [
        PROJECT_PATH.js + '/libs/jstree/jstree.min.js',
        PROJECT_PATH.js + '/libs/jstree/jstree.grid.min.js',
        PROJECT_PATH.js + '/modules/cms.pagetree.dropdown.js',
        PROJECT_PATH.js + '/modules/cms.pagetree.stickyheader.js',
        PROJECT_PATH.js + '/modules/cms.pagetree.js'
    ],
    'bundle.toolbar.min.js': [
        PROJECT_PATH.js + '/polyfills/function.prototype.bind.js',
        PROJECT_PATH.js + '/polyfills/array.prototype.findindex.js',
        PROJECT_PATH.js + '/libs/jquery.min.js',
        PROJECT_PATH.js + '/libs/class.min.js',
        PROJECT_PATH.js + '/libs/pep.js',
        PROJECT_PATH.js + '/modules/jquery.ui.custom.js',
        PROJECT_PATH.js + '/modules/jquery.ui.touchpunch.js',
        PROJECT_PATH.js + '/modules/jquery.ui.nestedsortable.js',
        PROJECT_PATH.js + '/modules/cms.base.js',
        PROJECT_PATH.js + '/modules/jquery.transition.js',
        PROJECT_PATH.js + '/modules/cms.messages.js',
        PROJECT_PATH.js + '/modules/cms.modal.js',
        PROJECT_PATH.js + '/modules/cms.sideframe.js',
        PROJECT_PATH.js + '/modules/cms.clipboard.js',
        PROJECT_PATH.js + '/modules/cms.plugins.js',
        PROJECT_PATH.js + '/modules/cms.structureboard.js',
        PROJECT_PATH.js + '/modules/cms.navigation.js',
        PROJECT_PATH.js + '/modules/cms.toolbar.js',
        PROJECT_PATH.js + '/modules/cms.tooltip.js'
    ]
};

var INTEGRATION_TESTS = [
    [
        'loginAdmin',
        'toolbar',
        'addFirstPage',
        'wizard',
        'editMode',
        'sideframe',
        'createContent',
        'users',
        'addNewUser',
        'newPage',
        'pageControl',
        'modal',
        'permissions',
        'logout',
        'clipboard'
    ],
    [
        'pageTypes',
        'switchLanguage',
        'editContent',
        'editContentTools',
        'publish',
        'loginToolbar',
        'changeSettings',
        'toolbar-login-apphooks',
        {
            serverArgs: '--CMS_PERMISSION=False --CMS_TOOLBAR_URL__EDIT_ON=test-edit',
            file: 'copy-from-language'
        },
        {
            serverArgs: '--CMS_PERMISSION=False --CMS_TOOLBAR_URL__EDIT_ON=test-edit',
            file: 'pagetree-no-permission'
        }
    ],
    [
        'pagetree',
        'disableToolbar',
        'dragndrop',
        'copy-apphook-page',
        'history',
        'revertLive',
        'narrowScreen'
    ]
];

var CMS_VERSION = fs.readFileSync('cms/__init__.py', { encoding: 'utf-8' })
    .match(/__version__ = '(.*?)'/)[1];

// #####################################################################################################################
// #TASKS#
/**
 * @function cacheBuster
 * @param {Object} opts
 * @param {String} [opts.version]
 * @returns {Function}
 */
var cacheBuster = function (opts) {
    var version = opts && opts.version ? opts.version : Math.random();

    return function (css) {
        css.replaceValues(/__VERSION__/g, { fast: '__VERSION__' }, function () {
            return version;
        });
    };
};

gulp.task('sass', function () {
    gulp.src(PROJECT_PATTERNS.sass)
        .pipe(gulpif(options.debug, sourcemaps.init()))
        .pipe(sass())
        .on('error', function (error) {
            gutil.log(gutil.colors.red('Error (' + error.plugin + '): ' + error.messageFormatted));
        })
        .pipe(postcss([
            autoprefixer({
                cascade: false
            }),
            cacheBuster({
                version: CMS_VERSION
            })
        ]))
        .pipe(minifyCss({
            rebase: false
        }))
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
    .on('glyphs', function (glyphs, opts) {
        gutil.log.bind(glyphs, opts);
    })
    .pipe(gulp.dest(PROJECT_PATH.icons));
});

gulp.task('lint', ['lint:javascript']);
gulp.task('lint:javascript', function () {
    // DOCS: http://eslint.org
    return gulp.src(PROJECT_PATTERNS.js)
        .pipe(eslint())
        .pipe(eslint.format())
        .pipe(eslint.failAfterError());
});

gulp.task('tests', ['tests:unit', 'tests:integration']);

// gulp tests:unit --tests=cms.base,cms.modal
gulp.task('tests:unit', function (done) {
    var server = new KarmaServer({
        configFile: PROJECT_PATH.tests + '/karma.conf.js',
        singleRun: true
    }, done);

    server.start();
});

gulp.task('tests:unit:watch', function () {
    var server = new KarmaServer({
        configFile: PROJECT_PATH.tests + '/karma.conf.js'
    });

    server.start();
});

// gulp tests:integration [--clean] [--screenshots] [--tests=loginAdmin,toolbar]
gulp.task('tests:integration', integrationTests({
    tests: INTEGRATION_TESTS,
    pathToTests: PROJECT_PATH.tests,
    argv: argv,
    dbPath: 'testdb.sqlite',
    serverCommand: 'testserver.py',
    logger: gutil.log.bind(gutil)
}));

Object.keys(JS_BUNDLES).forEach(function (bundleName) {
    var bundleFiles = JS_BUNDLES[bundleName];

    gulp.task('bundle:' + bundleName, function () {
        return gulp.src(bundleFiles)
            .pipe(gulpif(options.debug, sourcemaps.init()))
            .pipe(gulpif(!options.debug, uglify({
                preserveComments: 'some'
            })))
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

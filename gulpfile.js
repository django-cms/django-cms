// #####################################################################################################################
// #IMPORTS#
const gulp = require('gulp');
const gutil = require('gulp-util');
const plumber = require('gulp-plumber');
const fs = require('fs');
const autoprefixer = require('autoprefixer');
const postcss = require('gulp-postcss');
const browserSync = require('browser-sync').create();
const gulpif = require('gulp-if');
const iconfont = require('gulp-iconfont');
const iconfontCss = require('gulp-iconfont-css');
// const sass = require('gulp-sass');
const sass = require('gulp-sass')(require('sass'));
const sourcemaps = require('gulp-sourcemaps');
const minifyCss = require('gulp-clean-css');
const eslint = require('gulp-eslint');
const webpack = require('webpack');
const KarmaServer = require('karma').Server;
const integrationTests = require('djangocms-casper-helpers/gulp');
const GulpPostCss = require('gulp-postcss');

const argv = require('minimist')(process.argv.slice(2)); // eslint-disable-line

// #####################################################################################################################
// #SETTINGS#
const options = {
    debug: argv.debug
};
const PROJECT_ROOT = __dirname + '/cms/static/cms';
const PROJECT_PATH = {
    js: PROJECT_ROOT + '/js',
    sass: PROJECT_ROOT + '/sass',
    css: PROJECT_ROOT + '/css',
    icons: PROJECT_ROOT + '/fonts',
    tests: __dirname + '/cms/tests/frontend'
};

const PROJECT_PATTERNS = {
    js: [
        PROJECT_PATH.js + '/modules/*.js',
        PROJECT_PATH.js + '/widgets/*.js',
        PROJECT_PATH.js + '/*.js',
        PROJECT_PATH.tests + '/**/*.js',
        '!' + PROJECT_PATH.tests + '/unit/helpers/**/*.js',
        '!' + PROJECT_PATH.tests + '/coverage/**/*.js',
        '!' + PROJECT_PATH.js + '/modules/jquery.*.js',
        '!' + PROJECT_PATH.js + '/dist/*.js'
    ],
    sass: [PROJECT_PATH.sass + '/**/*.{scss,sass}'],
    icons: [PROJECT_PATH.icons + '/src/*.svg']
};

const INTEGRATION_TESTS = [
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
        'clipboard',
        'link-plugin-content-mode',
        'add-multiple-plugins',
        'plugin-dynamic-script-loading'
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
        'permissions-enabled',
        {
            serverArgs: '--CMS_PERMISSION=False --CMS_TOOLBAR_URL__EDIT_ON=test-edit',
            file: 'copy-from-language'
        },
        {
            serverArgs: '--CMS_PERMISSION=False --CMS_TOOLBAR_URL__EDIT_ON=test-edit',
            file: 'pagetree-no-permission'
        },
        {
            serverArgs: '--CMS_PERMISSION=False --CMS_TOOLBAR_URL__EDIT_ON=test-edit',
            file: 'permissions-disabled'
        }
    ],
    [
        'pagetree',
        'pagetree-drag-n-drop-copy',
        'disableToolbar',
        'dragndrop',
        'copy-apphook-page',
        // 'revertLive', // disabled
        'narrowScreen',
        'nonadmin'
    ]
];

const CMS_VERSION = fs.readFileSync('cms/__init__.py', { encoding: 'utf-8' }).match(/__version__ = '(.*?)'/)[1];

const css = () => {
    return (
        gulp
        .src(PROJECT_PATTERNS.sass)
        .pipe(gulpif(options.debug, sourcemaps.init()))
        .pipe(sass())
        .on('error', function(error) {
            gutil.log(gutil.colors.red('Error (' + error.plugin + '): ' + error.messageFormatted));
        })
        .pipe(
            postcss([
                autoprefixer({
                    cascade: false
                })
            ])
        )
        .pipe(
            minifyCss({
                rebase: false
            })
        )
        .pipe(gulpif(options.debug, sourcemaps.write()))
        .pipe(gulp.dest(PROJECT_PATH.css + '/' + CMS_VERSION + '/'))
    );
};

const icons = () => {
  return (
    gulp
        .src(PROJECT_PATTERNS.icons)
        .pipe(
            iconfontCss({
                fontName: 'django-cms-iconfont',
                path: PROJECT_PATH.sass + '/libs/_iconfont.scss',
                targetPath: '../../sass/components/_iconography.scss',
                fontPath: '../../fonts/' + CMS_VERSION + '/'
            })
        )
        .pipe(
            iconfont({
                fontName: 'django-cms-iconfont',
                normalize: true,
                formats: ['svg', 'ttf', 'eot', 'woff', 'woff2']
            })
        )
        .on('glyphs', function(glyphs, opts) {
            gutil.log.bind(glyphs, opts);
        })
        .pipe(gulp.dest(PROJECT_PATH.icons + '/' + CMS_VERSION + '/'))
  );
};

const lint = () => {
  return (
    gulp
        .src(PROJECT_PATTERNS.js)
        .pipe(gulpif(!process.env.CI, plumber()))
        .pipe(eslint())
        .pipe(eslint.format())
        .pipe(eslint.failAfterError())
        .pipe(gulpif(!process.env.CI, plumber.stop()))
  );
};

const unitTest = (done) => {
    return (
        new KarmaServer({
            configFile: PROJECT_PATH.tests + '/karma.conf.js',
            singleRun: true
        }, done).start()
    );
};

const testsIntegration = (done) => {
    integrationTests({
        tests: INTEGRATION_TESTS,
        pathToTests: PROJECT_PATH.tests,
        argv: argv,
        dbPath: 'testdb.sqlite',
        serverCommand: 'testserver.py',
        logger: gutil.log.bind(gutil),
        waitForMigrations: 5 // seconds
    });
    done();  
}

const webpackBundle = function(opts) {
    const webpackOptions = opts || {};

    webpackOptions.PROJECT_PATH = PROJECT_PATH;
    webpackOptions.debug = options.debug;
    webpackOptions.CMS_VERSION = CMS_VERSION;

    return function(done) {
        const config = require('./webpack.config')(webpackOptions);

        webpack(config, function(err, stats) {
            if (err) {
                throw new gutil.PluginError('webpack', err);
            }
            gutil.log('[webpack]', stats.toString({ maxModules: Infinity, colors: true, optimizationBailout: true }));
            if (typeof done !== 'undefined' && (!opts || !opts.watch)) {
                done();
            }
        });
    };
};

const watchFiles = () => {
    browserSync.init();
    gulp.watch(PROJECT_PATTERNS.sass, css);
    gulp.watch(PROJECT_PATTERNS.js, lint);
};

gulp.task("sass", css);
gulp.task("icons", icons);
gulp.task("lint", lint);
gulp.task('watch', gulp.parallel(watchFiles));
gulp.task('bundle', webpackBundle());
gulp.task('unitTest', unitTest);
gulp.task('testsIntegration',testsIntegration);
gulp.task('tests', gulp.series(unitTest, testsIntegration));
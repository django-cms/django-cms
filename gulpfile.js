// jshint node: true
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
var KarmaServer = require('karma').Server;
var child_process = require('child_process');
var spawn = require('child_process').spawn;

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
        '!' + PROJECT_PATH.js + '/modules/jquery.ui.*.js',
        '!' + PROJECT_PATH.js + '/dist/*.js'
    ],
    sass: [
        PROJECT_PATH.sass + '/**/*.{scss,sass}',
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
        PROJECT_PATH.js + '/polyfills/bind.js',
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
        PROJECT_PATH.js + '/modules/cms.pagetree.js',
    ],
    'bundle.toolbar.min.js': [
        PROJECT_PATH.js + '/polyfills/bind.js',
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
        // required for jscs
        .on('error', function (error) {
            gutil.log('\n' + error.message);
            if (process.env.CI) {
                // Force the process to exit with error code
                process.exit(1);
            }
        })
        .pipe(jshint.reporter('jshint-stylish'))
        .pipe(jshint.reporter('fail'));
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

// gulp tests:integration --tests=loginAdmin,toolbar
gulp.task('tests:integration', function (done) {
    process.env.PHANTOMJS_EXECUTABLE = './node_modules/.bin/phantomjs';

    var files = [
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
        'permissions',
        'pageTypes',
        'switchLanguage',
        'editContent',
        'editContentTools',
        'publish',
        'logout',
        'loginToolbar',
        'changeSettings',
        'disableToolbar',
        'dragndrop',
        'history',
        'revertLive',
        'narrowScreen',
        'clipboard',
        'modal'
    ];
    var pre = ['setup'];

    if (argv && argv.tests) {
        files = argv.tests.split(',');
        gutil.log('Running tests for ' + files.join(', '));
    }

    var tests = pre.concat(files).map(function (file) {
        return PROJECT_PATH.tests + '/integration/' + file + '.js';
    });

    // npm install -g casper-summoner
    if (argv && argv.summon) {
        child_process.execSync('casper-summoner ' + tests.join(' '));
        tests = tests.map(function (file) {
            return file.replace('.js', '.summoned.js');
        });
    }

    var casperChild = spawn('./node_modules/.bin/casperjs', ['test', '--web-security=no'].concat(tests));

    casperChild.stdout.on('data', function (data) {
        gutil.log('CasperJS:', data.toString().slice(0, -1));
    });

    casperChild.on('close', function (code) {
        if (argv && argv.summon) {
            child_process.execSync('rm ' + tests.join(' '));
        }

        done(code);
    });
});

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

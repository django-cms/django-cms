// #####################################################################################################################
// #IMPORTS#
const gulp = require('gulp');
const plumber = require('gulp-plumber');
const fs = require('fs');
const autoprefixer = require('autoprefixer');
const postcss = require('gulp-postcss');
const browserSync = require('browser-sync').create();
const gulpif = require('gulp-if');
const iconfont = require('gulp-iconfont');
const iconfontCss = require('gulp-iconfont-css');
const sass = require('gulp-sass')(require('sass'));
const sourcemaps = require('gulp-sourcemaps');
const minifyCss = require('gulp-clean-css');
const eslint = require('gulp-eslint-new');
const webpack = require('webpack');
const { Server: KarmaServer, config: karmaConfig } = require('karma');

// Logging utilities to replace gulp-util
const log = {
    info: (msg) => console.log('\x1b[36m%s\x1b[0m', msg),
    success: (msg) => console.log('\x1b[32m%s\x1b[0m', msg),
    error: (msg) => console.log('\x1b[31m%s\x1b[0m', msg),
    plain: (msg) => console.log(msg)
};

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
            log.error('Error (' + error.plugin + '): ' + error.messageFormatted);
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
            // Icon font glyphs generated
        })
        .pipe(gulp.dest(PROJECT_PATH.icons + '/' + CMS_VERSION + '/'))
  );
};

const lint = () => {
  const shouldFix = argv.fix || false;
  return (
    gulp
        .src(PROJECT_PATTERNS.js)
        .pipe(gulpif(!process.env.CI, plumber()))
        .pipe(eslint({ fix: shouldFix }))
        .pipe(eslint.format())
        .pipe(gulpif(shouldFix, gulp.dest((file) => file.base)))
        .pipe(eslint.failAfterError())
        .pipe(gulpif(!process.env.CI, plumber.stop()))
  );
};

const unitTest = async (done) => {
    try {
        const parsedConfig = await karmaConfig.parseConfig(
            PROJECT_PATH.tests + '/karma.conf.js',
            { singleRun: true },
            { promiseConfig: true, throwErrors: true }
        );
        const server = new KarmaServer(parsedConfig, (exitCode) => {
            if (exitCode !== 0) {
                done(new Error(`Karma tests failed with exit code ${exitCode}`));
                process.exit(exitCode);
            } else {
                done();
            }
        });
        server.start();
    } catch (error) {
        done(error);
    }
};

const testsIntegration = (done) => {
    const { spawn } = require('child_process');
    const http = require('http');

    const baseUrl = process.env.BASE_URL || 'http://localhost:9009';
    const port = argv.port || 9009;
    const serverArgs = argv.serverArgs || '';

    log.info('Starting Django test server...');

    // Start the test server - use .venv/bin/python if exists, otherwise system python
    const pythonCmd = fs.existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python';
    const serverProcess = spawn(pythonCmd, ['testserver.py', `--port=${port}`, ...serverArgs.split(' ').filter(Boolean)], {
        stdio: ['ignore', 'pipe', 'pipe'],
        cwd: __dirname
    });

    let serverOutput = '';
    serverProcess.stdout.on('data', (data) => {
        serverOutput += data.toString();
        if (options.debug) {
            process.stdout.write(data);
        }
    });

    serverProcess.stderr.on('data', (data) => {
        const errorMsg = data.toString();
        serverOutput += errorMsg;
        if (options.debug || errorMsg.includes('Error') || errorMsg.includes('Traceback')) {
            process.stderr.write(data);
        }
    });

    // Function to check if server is ready
    const checkServerReady = (retries = 30) => {
        return new Promise((resolve, reject) => {
            const checkInterval = setInterval(() => {
                http.get(`http://localhost:${port}`, (res) => {
                    if (res.statusCode === 200 || res.statusCode === 302) {
                        clearInterval(checkInterval);
                        log.success('✓ Test server is ready');
                        resolve();
                    }
                }).on('error', () => {
                    retries--;
                    if (retries <= 0) {
                        clearInterval(checkInterval);
                        reject(new Error('Test server failed to start'));
                    }
                });
            }, 1000);
        });
    };

    // Function to cleanup and exit
    const cleanup = (code, error) => {
        log.info('Stopping test server...');
        serverProcess.kill('SIGTERM');

        setTimeout(() => {
            if (!serverProcess.killed) {
                serverProcess.kill('SIGKILL');
            }
        }, 5000);

        if (error) {
            done(error);
        } else if (code !== 0) {
            done(new Error(`Playwright tests failed with exit code ${code}`));
        } else {
            log.success('✓ Playwright integration tests passed');
            done();
        }
    };

    // Wait for server to be ready, then run tests
    checkServerReady()
        .then(() => {
            log.info('Running Playwright integration tests...');

            const playwrightProcess = spawn('npx', ['playwright', 'test'], {
                stdio: 'inherit',
                shell: true,
                env: {
                    ...process.env,
                    BASE_URL: baseUrl
                }
            });

            playwrightProcess.on('exit', (code) => {
                cleanup(code);
            });

            playwrightProcess.on('error', (err) => {
                cleanup(1, err);
            });
        })
        .catch((err) => {
            cleanup(1, err);
        });

    // Handle process termination
    process.on('SIGINT', () => {
        cleanup(1, new Error('Process interrupted'));
    });
    process.on('SIGTERM', () => {
        cleanup(1, new Error('Process terminated'));
    });
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
                throw new Error('webpack: ' + err);
            }
            log.plain('[webpack] ' + stats.toString({ maxModules: Infinity, colors: true, optimizationBailout: true }));
            if (typeof done !== 'undefined' && (!opts || !opts.watch)) {
                done();
            }
        });
    };
};

// Build bundles and write detailed webpack stats to a JSON file for analysis
const webpackBundleStats = function(opts) {
    const webpackOptions = opts || {};
    webpackOptions.PROJECT_PATH = PROJECT_PATH;
    webpackOptions.debug = options.debug;
    webpackOptions.CMS_VERSION = CMS_VERSION;

    return function(done) {
        const config = require('./webpack.config')(webpackOptions);

        webpack(config, function(err, stats) {
            if (err) {
                throw new Error('webpack: ' + err);
            }
            // Generate a full stats JSON for maximum compatibility with analyzers
            const statsJson = stats.toJson({ all: true });
            try {
                fs.writeFileSync('webpack-stats.json', JSON.stringify(statsJson, null, 2));
                log.success('Wrote webpack-stats.json');
            } catch (e) {
                log.error('Failed to write webpack-stats.json: ' + e.message);
            }
            if (typeof done !== 'undefined' && (!opts || !opts.watch)) {
                done();
            }
        });
    };
};

// Analyze webpack-stats.json visually in the browser using webpack-bundle-analyzer
const analyzeWebpackStatsServer = (done) => {
    const statsFile = 'webpack-stats.json';
    const { spawn } = require('child_process');

    if (!fs.existsSync(statsFile)) {
        log.error('webpack-stats.json not found. Run `gulp bundle:stats` or use the combined task `gulp bundle:analyze`.');
        return done(new Error('webpack-stats.json not found'));
    }

    let analyzerCmd = 'webpack-bundle-analyzer';
    try {
        // Try to resolve to hint if package is missing
        require.resolve('webpack-bundle-analyzer');
    } catch (e) {
        log.error('webpack-bundle-analyzer is not installed. Install it with:');
        log.plain('  npm i -D webpack-bundle-analyzer');
        return done(new Error('webpack-bundle-analyzer missing'));
    }

    const port = argv.port || '8888';
    const host = argv.host || '127.0.0.1';
    // webpack-bundle-analyzer uses --no-open (there is no --open flag)
    const noOpenFlag = (argv.open === false || argv.noOpen) ? '--no-open' : '';
    const defaultSizes = argv.sizes || 'parsed'; // stat | parsed | gzip

    log.info(`Starting webpack-bundle-analyzer on http://${host}:${port} ...`);
    const bundleDir = PROJECT_PATH.js + '/dist/' + CMS_VERSION + '/';
    const proc = spawn('npx', [
        analyzerCmd,
        statsFile,
        bundleDir,
        '--mode', 'server',
        '--host', host,
        '--port', String(port),
        '--default-sizes', String(defaultSizes),
        noOpenFlag
    ].filter(Boolean), {
        stdio: 'inherit',
        shell: true
    });

    proc.on('exit', (code) => {
        if (code !== 0) {
            done(new Error(`webpack-bundle-analyzer exited with code ${code}`));
        } else {
            done();
        }
    });
};

// Generate a static HTML report for the current webpack-stats.json
const analyzeWebpackStatsStatic = (done) => {
    const statsFile = 'webpack-stats.json';
    const { spawn } = require('child_process');

    if (!fs.existsSync(statsFile)) {
        log.error('webpack-stats.json not found. Run `gulp bundle:stats` or use the combined task `gulp bundle:analyze:static`.');
        return done(new Error('webpack-stats.json not found'));
    }

    try {
        require.resolve('webpack-bundle-analyzer');
    } catch (e) {
        log.error('webpack-bundle-analyzer is not installed. Install it with:');
        log.plain('  npm i -D webpack-bundle-analyzer');
        return done(new Error('webpack-bundle-analyzer missing'));
    }

    const reportFile = argv.report || 'webpack-report.html';
    const defaultSizes = argv.sizes || 'parsed';

    log.info(`Generating static bundle analysis to ${reportFile} ...`);
    const staticBundleDir = PROJECT_PATH.js + '/dist/' + CMS_VERSION + '/';
    const proc = require('child_process').spawn('npx', [
        'webpack-bundle-analyzer',
        statsFile,
        staticBundleDir,
        '--mode', 'static',
        '--report', reportFile,
        '--default-sizes', String(defaultSizes),
        '--no-open'
    ], { stdio: 'inherit', shell: true });

    proc.on('exit', (code) => {
        if (code !== 0) {
            done(new Error(`webpack-bundle-analyzer (static) exited with code ${code}`));
        } else {
            log.success(`✓ Wrote ${reportFile}`);
            done();
        }
    });
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
gulp.task('bundle:stats', webpackBundleStats());
// Build + open interactive analyzer (server mode)
gulp.task('bundle:analyze', gulp.series(webpackBundleStats(), analyzeWebpackStatsServer));
// Build + generate a static HTML report (no server needed)
gulp.task('bundle:analyze:static', gulp.series(webpackBundleStats(), analyzeWebpackStatsStatic));
gulp.task('unitTest', unitTest);
gulp.task('testsIntegration',testsIntegration);
gulp.task('tests', gulp.series(unitTest, testsIntegration));

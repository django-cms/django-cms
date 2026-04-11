/*
 * Standalone gulpfile for the cms.contrib.frontend_v5 contrib app.
 *
 * Independent of the repo root gulpfile — the root build is untouched.
 * Run from anywhere via:
 *   npx gulp --gulpfile cms/contrib/frontend_v5/gulpfile.js <task>
 * or via the npm scripts in the root package.json (`npm run build:v5`).
 *
 * Tasks:
 *   build         — webpack + sass + vendor production build
 *   build:dev     — same, with sourcemaps and no minification
 *   watch         — webpack watch mode (use `sass` separately for CSS)
 *   sass          — compile src/sass/cms.*.scss → static/cms/css/<CMS_VERSION>/
 *   copy-vendor   — copy vendor assets (tom-select default CSS) into the
 *                   drop-in paths that legacy code expects (e.g.
 *                   /static/cms/js/select2/select2.css is shadowed with
 *                   Tom Select styles since PageSmartLinkWidget's Django
 *                   form.Media still references that URL).
 *   typecheck     — tsc --noEmit against ./tsconfig.json
 *   test          — vitest run
 *   default       — typecheck + (build ∥ sass ∥ copy-vendor)
 *
 * Shares the root node_modules — no nested npm install required.
 */
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const gulp = require('gulp');
const webpack = require('webpack');
const minimist = require('minimist');
const gulpSass = require('gulp-sass')(require('sass'));
const postcss = require('gulp-postcss');
const autoprefixer = require('autoprefixer');
const cleanCSS = require('gulp-clean-css');
const sourcemaps = require('gulp-sourcemaps');
const gulpif = require('gulp-if');

const APP_ROOT = __dirname;
const REPO_ROOT = path.resolve(APP_ROOT, '..', '..', '..');
const argv = minimist(process.argv.slice(2));

const log = {
    info: (msg) => console.log('\x1b[36m%s\x1b[0m', msg),
    success: (msg) => console.log('\x1b[32m%s\x1b[0m', msg),
    error: (msg) => console.log('\x1b[31m%s\x1b[0m', msg),
    plain: (msg) => console.log(msg),
};

// Read CMS version from cms/__init__.py so the build output mirrors the
// legacy bundle's `dist/<CMS_VERSION>/` layout — keeps versioned cache
// behaviour consistent across both stacks.
const CMS_VERSION = fs
    .readFileSync(path.join(REPO_ROOT, 'cms', '__init__.py'), { encoding: 'utf-8' })
    .match(/__version__ = '(.*?)'/)[1];

function buildWebpack(opts) {
    const webpackOpts = {
        debug: !!opts.debug,
        watch: !!opts.watch,
        CMS_VERSION,
    };
    return function (done) {
        const config = require('./webpack.config')(webpackOpts);
        webpack(config, function (err, stats) {
            if (err) {
                done(new Error('webpack(v5): ' + err));
                return;
            }
            log.plain('[webpack v5] ' + stats.toString({ colors: true }));
            if (stats.hasErrors()) {
                done(new Error('frontend_v5 build failed'));
                return;
            }
            if (!webpackOpts.watch) done();
        });
    };
}

function runNpx(args, opts = {}) {
    return function (done) {
        const proc = spawn('npx', args, {
            stdio: 'inherit',
            shell: true,
            cwd: opts.cwd || REPO_ROOT,
            env: { ...process.env, ...(opts.env || {}) },
        });
        proc.on('exit', (code) => {
            if (code !== 0) {
                done(new Error(`${args.join(' ')} exited with code ${code}`));
            } else {
                done();
            }
        });
        proc.on('error', (err) => done(err));
    };
}

const build = buildWebpack({ debug: false });
const buildDev = buildWebpack({ debug: true });
const watch = buildWebpack({ debug: true, watch: true });

// SCSS build. Inputs are the top-level `cms.*.scss` entries in src/sass/;
// partials (files prefixed with `_`) are imported by them and skipped as
// compilation targets automatically by gulp-sass. Output lands at the
// legacy-matching path so the drop-in contract in CLAUDE.md holds: when
// `cms.contrib.frontend_v5` is first in INSTALLED_APPS, these files
// shadow `cms/static/cms/css/<CMS_VERSION>/*.css`.
function sass() {
    const debug = !!argv.debug;
    return gulp
        .src(path.join(APP_ROOT, 'src', 'sass', '**', '*.scss'))
        .pipe(gulpif(debug, sourcemaps.init()))
        .pipe(gulpSass({ outputStyle: 'expanded' }).on('error', gulpSass.logError))
        .pipe(postcss([autoprefixer()]))
        .pipe(
            cleanCSS({
                level: {
                    2: {
                        all: false,
                        removeDuplicateRules: true,
                    },
                },
            }),
        )
        .pipe(gulpif(debug, sourcemaps.write('.')))
        .pipe(
            gulp.dest(
                path.join(APP_ROOT, 'static', 'cms', 'css', CMS_VERSION),
            ),
        );
}

const typecheck = runNpx([
    'tsc',
    '--noEmit',
    '-p',
    path.relative(REPO_ROOT, path.join(APP_ROOT, 'tsconfig.json')),
]);

const test = runNpx([
    'vitest',
    'run',
    '--config',
    path.relative(REPO_ROOT, path.join(APP_ROOT, 'vitest.config.ts')),
]);

exports.build = gulp.parallel(build, sass);
exports['build:dev'] = gulp.parallel(buildDev, sass);
exports['build:js'] = build;
exports.watch = watch;
exports.sass = sass;
exports.typecheck = typecheck;
exports.test = test;
exports.default = gulp.series(typecheck, gulp.parallel(build, sass));

var gutil = require('gulp-util');
var iconfont = require('gulp-iconfont');
var iconfontCss = require('gulp-iconfont-css');

module.exports = function (gulp, opts) {
    return function () {
        gulp.src(opts.PROJECT_PATH.icons + '/**/*.svg')
            .pipe(iconfontCss({
                fontName: 'iconfont',
                appendUnicode: true,
                formats: ['ttf', 'eot', 'woff', 'svg'],
                fontPath: 'static/fonts/',
                path: opts.PROJECT_PATH.sass + '/libs/_iconfont.scss',
                targetPath: '../../../private/sass/layout/_iconography.scss'
            }))
            .pipe(iconfont({
                fontName: 'iconfont',
                normalize: true
            }))
            .on('glyphs', function (glyphs, options) {
                gutil.log.bind(glyphs, options);
            })
            .pipe(gulp.dest(opts.PROJECT_PATH.fonts));
    };
};

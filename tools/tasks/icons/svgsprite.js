const gutil = require('gulp-util');
const svgSprites = require('gulp-svg-sprites');

module.exports = function(gulp, opts) {
    return function() {
        // https://github.com/shakyshane/gulp-svg-sprites
        const config = {
            mode: 'symbols',
            preview: true,
            svgPath: `../sprites/${opts.svg}.svg`,
            svg: {
                symbols: `${opts.PROJECT_PATH.sprites}/${opts.svg}.svg`,
            },
        };

        return (
            gulp
                .src(opts.PROJECT_PATTERNS.svg[opts.svg])
                .pipe(svgSprites(config))
                .on('error', function(error) {
                    gutil.log(gutil.colors.red('Error (' + error.plugin + '): ' + error.messageFormatted));
                })
                // needs to be PROJECT_ROOT as the svgSprite config will do the rest
                .pipe(gulp.dest(opts.PROJECT_ROOT))
        );
    };
};

const fs = require('fs');
const gutil = require('gulp-util');
const svgSprites = require('gulp-svg-sprites');


module.exports = function (gulp, opts) {
    return function () {
        // https://github.com/shakyshane/gulp-svg-sprites
        const config = {
            baseSize: 16,
            preview: false,
            templates: {
                scss: fs.readFileSync(opts.PROJECT_PATH.sass + '/libs/_svgsprite.scss', 'utf-8'),
            },
            selector: 'icon-%f',
            svgPath: '../sprites/icons.svg',
            svg: {
                sprite: opts.PROJECT_PATH.sprites + '/icons.svg',
            },
            cssFile: opts.PROJECT_PATH.sass + '/components/_icons.scss',
        };

        return gulp.src(opts.PROJECT_PATTERNS.svg)
            .pipe(svgSprites(config))
            .on('error', function (error) {
                gutil.log(gutil.colors.red(
                    'Error (' + error.plugin + '): ' + error.messageFormatted)
                );
            })
            // needs to be PROJECT_ROOT as the svgSprite config will do the rest
            .pipe(gulp.dest(opts.PROJECT_ROOT));
    };
};

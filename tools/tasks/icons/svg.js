const gutil = require('gulp-util');
const svgSprite = require('gulp-svg-sprite');


module.exports = function (gulp, opts) {
    return function () {
        // https://github.com/jkphl/svg-sprite#configuration-basics
        const config = {
            mode: {
                css: {
                    sprite: opts.PROJECT_PATH.sprites + '/icons',
                    render: {
                        scss: {
                            dest: opts.PROJECT_PATH.sass + '/components/_icons',
                            template: opts.PROJECT_PATH.sass + '/libs/_svgsprite.scss'
                        }
                    },
                    variables: {
                        mapname: 'icons'
                    }
                }
            }
        };

        return gulp.src(opts.PROJECT_PATTERNS.svg)
            .pipe(svgSprite(config))
            .on('error', function (error) {
                gutil.log(gutil.colors.red(
                    'Error (' + error.plugin + '): ' + error.messageFormatted)
                );
            })
            // needs to be PROJECT_ROOT as the svgSprite config will do the rest
            .pipe(gulp.dest(opts.PROJECT_ROOT));
    };
};

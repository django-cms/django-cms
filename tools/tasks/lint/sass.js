const styleLint = require('gulp-stylelint');


module.exports = function (gulp, opts) {
    return function () {
        return gulp.src(opts.PROJECT_PATTERNS.sass)
            .pipe(styleLint({
                configFile: opts.PROJECT_PATH.sass + '/.stylelintrc.js',
                reporters: [{
                    formatter: (opts.argv.debug) ? 'verbose' : 'string',
                    console: true
                }]
            }));
    };
};

const file = require('gulp-file');
const fs = require('fs');

module.exports = function(gulp, opts) {
    return function() {
        const list = fs.readdirSync(opts.PROJECT_PATH.svg + '/' + opts.svg).map(file =>
            `"${file.replace(/\.svg$/, '')}"`
        ).join(',\n');

        const content = `
            {
                "svg": true,
                "spritePath": "sprites/${opts.svg}.svg",
                "iconClass": "icon",
                "iconClassFix": "icon-",
                "icons": [
                    ${list}
                ]
            }
        `;

        return (
           file('iconset.json', content, { src: true })
                .pipe(gulp.dest(opts.PROJECT_ROOT + '/static'))
        );
    };
};

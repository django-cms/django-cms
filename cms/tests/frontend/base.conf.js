'use strict';

// #############################################################################
// CONFIGURATION

var b2s = require('browserslist-saucelabs');

module.exports = {
    formatTaskName: function formatTaskName(browserName) {
        return [
            'Test', browserName, 'for',
            process.env.TRAVIS_REPO_SLUG,
            process.env.TRAVIS_PULL_REQUEST === 'false' ?
            '' : 'pull request #' + process.env.TRAVIS_PULL_REQUEST,
            'build #' + process.env.TRAVIS_JOB_NUMBER
        ].join(' ');
    },

    // limiting browsers for saucelabs here
    // because ios and ms edge are currently broken
    // because there's an issue with socket.io / karma and
    // we have to wait for releases that include https://github.com/socketio/socket.io-client/issues/898
    sauceLabsBrowsers: b2s({ browsers: 'chrome 46, ff 41, ie 11, ie 10, safari 7' })
};

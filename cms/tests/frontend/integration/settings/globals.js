'use strict';

// #############################################################################
// Global values, used throughout the test suites
// TODO update with actual data

module.exports = {
    // plain Django admin login window title looks like this:
    websiteName: 'Log in | Django site admin',
    // TODO:
    // - configure languages with djangocms-helper
    // - remove hardcoded host, port, language values
    baseUrl: 'http://localhost:8000/en/',
    editUrl: 'http://localhost:8000/en/?edit',
    editOffUrl: 'http://localhost:8000/en/?edit_off',
    credentials: {
        // djangocms helper creates such a user by default
        username: 'admin',
        password: 'admin'
    }
};

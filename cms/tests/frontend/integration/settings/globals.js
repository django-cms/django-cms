'use strict';

// #############################################################################
// Global values, used throughout the test suites
// TODO update with actual data

module.exports = {
    adminTitle: 'Log in | Django site admin',
    toolbarTransitionTime: 200,
    // TODO:
    // - configure languages with djangocms-helper
    // - remove hardcoded host, port, language values
    baseUrl: 'http://localhost:8000/en/',
    editUrl: 'http://localhost:8000/en/?edit',
    editOffUrl: 'http://localhost:8000/en/?edit_off',
    adminUrl: 'http://localhost:8000/en/admin/login/',
    credentials: {
        username: 'admin',
        password: 'admin'
    },
    content: {
        page: {
            title: 'First page',
            text: 'First page content'
        }
    },
    user: {
        // TODO add more data for the new user profile
        firstName: 'test-first-name'
    }
};

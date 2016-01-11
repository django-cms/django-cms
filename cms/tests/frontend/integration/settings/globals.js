'use strict';

// #############################################################################
// Global values, used throughout the test suites
// TODO update with actual data

module.exports = {
    adminTitle: 'Log in | Django site admin',
    // TODO:
    // - configure languages with djangocms-helper
    // - remove hardcoded host, port, language values
    baseUrl: 'http://localhost:8000/en/',
    editUrl: 'http://localhost:8000/en/?edit',
    editOffUrl: 'http://localhost:8000/en/?edit_off',
    adminUrl: 'http://localhost:8000/en/admin/login/',
    adminLogoutUrl: 'http://localhost:8000/en/admin/logout/',
    adminPagesUrl: 'http://localhost:8000/en/admin/cms/page/',
    adminPageUsers: 'http://localhost:8000/en/admin/auth/user/',
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
        firstName: 'test-first-name',
        lastName: 'test-last-name',
        userEmail: 'test@email.com',
        addUsername: 'test-add-user',
        addPassword1: 'test',
    }
};

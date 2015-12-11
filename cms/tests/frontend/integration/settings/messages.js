'use strict';

// #############################################################################
// Global values, used throughout the test suites

module.exports = {
    login: {
        admin: {
            cmsTitleOk: 'The CMS is available and admin panel title is correct',
            adminAvailable: 'Admin login form is available',
            loginFail: 'login with wrong credentials failed',
            loginOk: 'Login via the admin form done'
        },
        toolbar: {
            cmsAvailable: ' and page title is correct',
            toolbarMissing: 'Toolbar isn\'t originally available',
            toolbarAvailable: 'Toolbar opened by appending /?edit to the url',
            loginOk: 'Login via the toolbar form'
        }
    },
    toolbar: {
        logoUrlCorrect: 'The django CMS logo redirects to homepage',
        toolbarOpened: 'Toolbar can be opened on trigger click',
        toolbarClosed: 'Toolbar can be closed on trigger click'
    },
    logout: {
        toolbarEditOn: 'Toolbar opened by appending /?edit to the url',
        toolbarEditOff: 'Toolbar closed by appending /?edit_off to the url',
        logoutOk: 'Logout via the toolbar done'
    },
    page: {

    }
};

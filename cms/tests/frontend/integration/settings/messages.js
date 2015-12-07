'use strict';

// #############################################################################
// Global values, used throughout the test suites

module.exports = {
    login: {
        cmsAvailable: 'The CMS is available and page title is correct',
        toolbarMissing: 'Toolbar isn\'t originally available',
        toolbarAvailable: 'Toolbar opened by appending /?edit to the url',
        loginOk: 'Login via the toolbar form'
    },
    toolbar: {
        logoUrlCorrect: 'The django CMS logo redirects to homepage',
        toolbarOpened: 'Toolbar can be opened',
        toolbarClosed: 'Toolbar can be closed'
    },
    logout: {

    }
};

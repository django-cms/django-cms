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
            toolbarAvailable: 'The toolbar login form is available',
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
        creation: {
            created: 'The new page has been created and its content is correct',
            published: 'The new page has been published',
            wizard: {
                opened: 'The wizard pop up is opened',
                closed: 'The wizard pop up is closed',
                formAvailable: 'The page creation wizard form is available'
            },
            admin: {

            }
        },
        addContent: {
            noEmptyPlugin: 'Empty plugin haven\'t been created',
            noFilteredResults: 'No filtered results for random string',
            filteredPluginAvailable: 'There is text plugin available by filter: text',
            newPluginVisible: 'Newly created text plugin can be seen on page'
        }
    }
};

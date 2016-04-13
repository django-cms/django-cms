'use strict';

// #############################################################################
// Global values, used throughout the test suites
// TODO update with actual data

function configure(opts) {
    var port = opts && typeof opts.port !== 'undefined' ? opts.port : 8000;
    var editOn = opts && typeof opts.editOn !== 'undefined' ? opts.editOn : 'edit';
    var editOff = opts && typeof opts.editOff !== 'undefined' ? opts.editOff : 'edit_off';
    var config = {
        adminTitle: 'Log in | Django site admin',
        // TODO:
        // - configure languages with djangocms-helper
        // - remove hardcoded host, port, language values
        baseUrl: 'http://localhost:' + port + '/en/',
        editUrl: 'http://localhost:' + port + '/en/?' + editOn,
        editOffUrl: 'http://localhost:' + port + '/en/?edit_off',
        adminUrl: 'http://localhost:' + port + '/en/admin/login/',
        adminLogoutUrl: 'http://localhost:' + port + '/en/admin/logout/',
        adminPagesUrl: 'http://localhost:' + port + '/en/admin/cms/page/',
        adminUsersUrl: 'http://localhost:' + port + '/en/admin/auth/user/',
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
            firstName: 'test-first-name',
            lastName: 'test-last-name',
            userEmail: 'test@email.com',
            username: 'test-add-user',
            password: 'test'
        }
    };

    return config;
}

module.exports = configure();
module.exports.configure = configure;

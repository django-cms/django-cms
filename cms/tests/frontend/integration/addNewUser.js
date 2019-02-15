'use strict';

var helpers = require('djangocms-casper-helpers');
var globals = helpers.settings;
var cms = helpers();
var casperjs = require('casper');
var xPath = casperjs.selectXPath;

casper.test.setUp(function(done) {
    casper.start().then(cms.login()).then(cms.addPage({ title: 'home' })).run(done);
});

casper.test.tearDown(function(done) {
    casper.start().then(cms.removePage()).then(cms.logout()).run(done);
});

casper.test.begin('Add New User', function(test) {
    casper
        .start(globals.editUrl)
        // click on example
        .waitForSelector('.cms-toolbar-expanded', function() {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        // click on Users
        .waitUntilVisible('.cms-toolbar-item-navigation-hover a', function() {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/en/admin/auth/user/"]');
        })
        // waits for sideframe to open
        .waitUntilVisible('.cms-sideframe-frame')
        .withFrame(0, function() {
            casper
                .waitForSelector('#content-main', function() {
                    test.assertExists('.addlink', 'Add User Button exists');

                    // clicks on add user
                    this.click('.object-tools a[href$="/en/admin/auth/user/add/"]');
                })
                // inserts the username and pw in the form fields
                .waitUntilVisible('.form-row', function() {
                    test.assertExists('#user_form', 'Username input field exists');
                    this.fill(
                        '#user_form',
                        {
                            username: globals.user.username,
                            password1: globals.user.password,
                            password2: globals.user.password
                        },
                        true
                    );
                })
                .waitForSelector('#user_form', function() {
                    test.assertField('username', globals.user.username, 'Username has been added');
                })
                .waitForSelector('.success', function() {
                    test.assertExists('.success', 'The user was added successfully. You may edit it again below.');

                    // adds firs name, last name, email and enables superuser and stuff
                    this.fill(
                        '#user_form',
                        {
                            first_name: globals.user.firstName,
                            last_name: globals.user.lastName,
                            email: globals.user.userEmail,
                            is_staff: true,
                            is_superuser: true
                        },
                        true
                    );
                })
                // checks if the user has been added to the list
                .waitForSelector('#changelist-form', function() {
                    test.assertSelectorHasText(
                        '#changelist-form .field-email',
                        globals.user.userEmail,
                        'The User has been updated'
                    );
                })
                .then(cms.logout())
                // checks if logout was successful
                .then(function() {
                    test.assertDoesntExist('.cms-toolbar-trigger', 'User logout');
                })
                // logins with the parameters of the new created user
                .then(
                    cms.login({
                        username: globals.user.username,
                        password: globals.user.password
                    })
                )
                .thenOpen(globals.adminUrl)
                .then(function() {
                    test.assertExist('#content-main', 'User logged in');
                })
                // goes directly into the Users Page
                .thenOpen(globals.adminUsersUrl)
                .waitForSelector('#changelist-form', function() {
                    test.assertExists('#changelist-form', 'User Page has been loaded');
                })
                .waitForSelector('.field-username', function() {
                    this.mouse.click(
                        // xPath searches the th tag with an a tag which contains the name of the user "test-add-user"
                        xPath('//th[@class="field-username"][./a[text()[contains(.,"test-add-user")]]]/a')
                    );
                })
                // delete button gets clicked
                .waitForSelector('#user_form', function() {
                    test.assertExists('#user_form', 'User Form has been loaded');
                    this.click('.deletelink');
                })
                // confirming that the user gets deleted
                .waitForSelector('.delete-confirmation', function() {
                    test.assertExists('.delete-confirmation', 'Delete button clicked confirmed');
                    this.click('input[type="submit"]');
                })
                // checks if user is removed from the list
                .waitForSelector('.success', function() {
                    test.assertDoesntExist(
                        xPath('//th[@class="field-username"][./a[text()[contains(.,"test-add-user")]]]'),
                        'deleted successfully'
                    );

                    test.assertExist('.login', 'login screens appears');
                })
                // logins again with the admin user
                .then(cms.login());
        })
        .run(function() {
            test.done();
        });
});

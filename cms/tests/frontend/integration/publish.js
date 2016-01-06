/* global DateTimeShortcuts */
'use strict';

// #############################################################################
// Publishing a page with a publish date

var globals = require('./settings/globals');
var messages = require('./settings/messages').page.publish;
var cms = require('./helpers/cms')();

casper.test.setUp(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.addPage({ title: 'First page' }))
        .then(cms.addPage({ title: 'Second' })) // we rely on slug being "/second"
        .run(done);
});

casper.test.tearDown(function (done) {
    casper.start()
        .then(cms.login())
        .then(cms.removePage())
        .then(cms.removePage())
        .then(cms.logout())
        .run(done);
});

    var pageTitle;
    var publishDate;
    var publishTime;

    casper
        .start(globals.editUrl)
        // opening an unpublished new page
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.nav li:nth-child(2) a');
        })
        // checking that it isn't published, storing its' url and opening Page menu
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            pageTitle = this.getTitle();
            pageUrl = (globals.baseUrl + pageTitle).toLowerCase() + '/';

            test.assertSelectorHasText(
                '.cms-publish-page',
                'Publish page now',
                'Unpublished page has been opened'
            );

            this.click('.cms-toolbar-item-navigation > li:nth-child(2) > a');
        })
        // opening "Publishing dates" menu item
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/dates/"]');
        })
        .withFrame(0, function () {
            casper
                // updating the publish time in the field and grabbing that value
                .waitUntilVisible('#page_form', function () {
                    publishDate = this.evaluate(function () {
                        DateTimeShortcuts.handleCalendarQuickLink(0, 0);
                        return $('#id_publication_date_0').val();
                    });

                    publishTime = this.evaluate(function () {
                        DateTimeShortcuts.handleClockQuicklink(0, -1);
                        return $('#id_publication_date_1').val();
                    });
                })
                .then(function () {
                    // publish time is in a minute
                    var year = publishDate.substring(0, 4);
                    var month = publishDate.substring(5, 7);
                    var day = publishDate.substring(8, 10);
                    var hours = publishTime.substring(0, 2);
                    var minutes = publishTime.substring(3, 5);
                    var seconds = publishTime.substring(6, 8);

                    // adding one minute to the publish time
                    var timestamp = new Date(year, month, day, hours, minutes, seconds);
                    timestamp.setMinutes(timestamp.getMinutes() + 1);

                    publishTime = timestamp.getHours() + ':' + timestamp.getMinutes() + ':' + timestamp.getSeconds();

                    this.fill('#page_form', {
                        publication_date_1: publishTime
                    });
                });
        })
        // submitting the updated publish time
        .then(function () {
            this.click('.cms-modal .cms-btn-action');
        })
        // clicking on 'Publish page now' button
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            // handles confirm popup
            this.setFilter('page.confirm', function () {
                return true;
            });

            this.click('.cms-btn-publish');
        })
        // logging out
        .thenOpen(globals.editUrl)
        .waitUntilVisible('.cms-toolbar-expanded', function () {
            this.click('.cms-toolbar-item-navigation li:first-child a');
        })
        .waitForSelector('.cms-toolbar-item-navigation-hover', function () {
            this.click('.cms-toolbar-item-navigation-hover a[href$="/admin/logout/"]');
        })
        .waitForSelector('body', function () {
            test.assertDoesntExist('.cms-toolbar', 'Successfully logged out');

            casper.echo(globals.baseUrl);
            casper.echo(pageUrl);

        })
        // going to the newly created page url and checking that it hasn't been published yet
        .thenOpen(pageUrl, function () {
            test.assertTitle('Page not found', 'The page is not yet available');
        })
        // trying the same in a minute
        .wait(60000)
        .thenOpen(pageUrl, function () {
            test.assertTitle(pageTitle, 'The page is published and available');
        })
        .run(function () {
            this.removeAllFilters('page.confirm');
            test.done();
        });
});

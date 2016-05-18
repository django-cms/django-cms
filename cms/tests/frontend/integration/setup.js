// #############################################################################
// Init all settings and event handlers on suite start
'use strict';

require('./../casperjs.conf').init();

require('./handlers/pageErrors').bind();
require('./handlers/loadFailures').bind();
require('./handlers/missingPages').bind();
require('./handlers/externalMissing').bind();
require('./handlers/suiteFailures').bind();

casper.test.done();

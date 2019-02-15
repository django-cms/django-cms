// #############################################################################
// Init all settings and event handlers on suite start
'use strict';

require('./../casperjs.conf').init();

require('./handlers/pageErrors').bind();
require('./handlers/loadFailures').bind();
require('./handlers/missingPages').bind();
require('./handlers/externalMissing').bind();
require('./handlers/suiteFailures').bind();

// eslint-disable-next-line
function show(casper, port) {
    if (!casper.started) {
        return;
    }
    casper.evaluate(function(opts) {
        var options = JSON.parse(opts);
        var img = options.img;
        var visualPort = options.port;
        // eslint-disable-next-line
        __utils__.sendAJAX('http://localhost:' + visualPort, 'POST', { img: img }, false);
    }, JSON.stringify({ img: casper.captureBase64('png'), port: port }));
}

if (casper.cli.options.visual) {
    var port = casper.cli.options['visual-port'];

    setInterval(function() {
        show(casper, port);
    }, parseInt(casper.cli.options.visual, 10));
}

casper.test.done();

'use strict';

// #############################################################################
// Handles JavaScript page errors

module.exports = {
    bind: function() {
        casper.on('page.error', function(msg, trace) {
            casper.echo('Error on page: ' + JSON.stringify(msg), 'ERROR');
            casper.echo('Traceback:', 'ERROR');
            var traceback = trace.reduce(function(message, part) {
                return message + 'at ' + part.function + ' (' + part.file + ':' + part.line + ')\n    ';
            }, '   ');
            casper.echo(traceback, 'ERROR');
        });
    }
};

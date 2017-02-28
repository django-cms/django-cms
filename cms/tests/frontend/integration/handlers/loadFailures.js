'use strict';

// #############################################################################
// Handles load failure errors

module.exports = {
    bind: function () {
        casper.on('load.failed', function (error) {
            casper.echo(JSON.stringify(error), 'ERROR');
        });
    }
};

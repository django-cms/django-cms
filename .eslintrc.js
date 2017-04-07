'use strict';

module.exports = {
    // documentation about rules can be found on http://eslint.org/docs/user-guide/configuring
    // based on http://eslint.org/docs/user-guide/configuring
    'extends': 'eslint:recommended',
    // http://eslint.org/docs/user-guide/configuring.html#specifying-environments
    'env': {
        'browser': true,
        'node': true,
        'jquery': true,
        'es6': true,
    },
    'parser': 'babel-eslint',
    'parserOptions': {
        'sourceType': 'module',
    },
    'rules': {
        // 0 = ignore, 1 = warning, 2 = error
        'indent': [2, 4],
        'quotes': [1, 'single'],
        'comma-dangle': [1, 'always-multiline'],
    },
}

const babelParser = require('@babel/eslint-parser');
const compatPlugin = require('eslint-plugin-compat');
const js = require('@eslint/js');

module.exports = [
    js.configs.recommended,
    {
        files: ['**/*.js'],
        languageOptions: {
            ecmaVersion: 2020,
            sourceType: 'module',
            parser: babelParser,
            parserOptions: {
                requireConfigFile: false,
                babelOptions: {
                    presets: ['@babel/preset-env']
                }
            },
            globals: {
                // Browser globals
                window: 'readonly',
                document: 'readonly',
                navigator: 'readonly',
                console: 'readonly',
                setTimeout: 'readonly',
                clearTimeout: 'readonly',
                setInterval: 'readonly',
                clearInterval: 'readonly',
                Promise: 'readonly',
                localStorage: 'readonly',
                sessionStorage: 'readonly',
                CustomEvent: 'readonly',
                Event: 'readonly',
                Node: 'readonly',
                history: 'readonly',
                location: 'readonly',
                alert: 'readonly',
                confirm: 'readonly',
                prompt: 'readonly',

                // jQuery
                $: 'readonly',
                jQuery: 'readonly',

                // Jasmine
                jasmine: 'readonly',
                describe: 'readonly',
                it: 'readonly',
                expect: 'readonly',
                beforeEach: 'readonly',
                afterEach: 'readonly',
                beforeAll: 'readonly',
                afterAll: 'readonly',
                spyOn: 'readonly',
                spyOnEvent: 'readonly',
                pending: 'readonly',
                fixture: 'readonly',

                // Custom globals
                CMS: 'readonly',
                __CMS_VERSION__: 'readonly',

                // Node.js (for build scripts)
                process: 'readonly',
                __dirname: 'readonly',
                __filename: 'readonly',
                module: 'readonly',
                require: 'readonly',
                exports: 'writable',
                Buffer: 'readonly'
            }
        },
        plugins: {
            compat: compatPlugin
        },
        settings: {
            polyfills: ['document-currentscript']
        },
        rules: {
            // Possible Errors
            'comma-dangle': ['error', 'never'],
            'no-cond-assign': 'error',
            'no-console': 'warn',
            'no-constant-condition': 'error',
            'no-control-regex': 'error',
            'no-debugger': 'error',
            'no-dupe-args': 'error',
            'no-dupe-keys': 'error',
            'no-duplicate-case': 'error',
            'no-empty-character-class': 'error',
            'no-empty': ['error', { allowEmptyCatch: true }],
            'no-ex-assign': 'error',
            'no-extra-boolean-cast': 'error',
            'no-extra-parens': 'off',
            'no-extra-semi': 'error',
            'no-func-assign': 'error',
            'no-inner-declarations': 'error',
            'no-invalid-regexp': 'error',
            'no-irregular-whitespace': 'error',
            'no-obj-calls': 'error',
            'no-regex-spaces': 'error',
            'no-sparse-arrays': 'error',
            'no-unexpected-multiline': 'error',
            'no-unreachable': 'error',
            'use-isnan': 'error',
            'valid-typeof': 'error',

            // Best Practices
            'accessor-pairs': 'error',
            'block-scoped-var': 'error',
            'complexity': ['error', { max: 10 }],
            'consistent-return': 'off',
            'curly': 'error',
            'default-case': 'error',
            'dot-location': ['error', 'property'],
            'dot-notation': 'error',
            'eqeqeq': 'error',
            'guard-for-in': 'error',
            'no-alert': 'error',
            'no-caller': 'error',
            'no-case-declarations': 'error',
            'no-div-regex': 'error',
            'no-else-return': 'warn',
            'no-empty-pattern': 'error',
            'no-eq-null': 'error',
            'no-eval': 'error',
            'no-extend-native': 'error',
            'no-extra-bind': 'error',
            'no-fallthrough': 'error',
            'no-floating-decimal': 'error',
            'no-implicit-coercion': 'off',
            'no-implied-eval': 'error',
            'no-invalid-this': 'off',
            'no-iterator': 'error',
            'no-labels': 'error',
            'no-lone-blocks': 'error',
            'no-loop-func': 'error',
            'no-magic-numbers': [
                'error',
                {
                    ignore: [0, -1, 1, 2],
                    ignoreArrayIndexes: true
                }
            ],
            'no-multi-spaces': 'error',
            'no-multi-str': 'off',
            'no-new-func': 'error',
            'no-new-wrappers': 'error',
            'no-new': 'off',
            'no-octal-escape': 'error',
            'no-octal': 'error',
            'no-param-reassign': 'error',
            'no-proto': 'error',
            'no-redeclare': 'error',
            'no-return-assign': 'error',
            'no-script-url': 'error',
            'no-self-compare': 'error',
            'no-sequences': 'error',
            'no-throw-literal': 'error',
            'no-unused-expressions': ['error', { allowShortCircuit: true }],
            'no-useless-call': 'error',
            'no-useless-concat': 'error',
            'no-void': 'error',
            'no-warning-comments': 'off',
            'no-with': 'error',
            'radix': 'error',
            'vars-on-top': 'off', // FIXME should be enabled at some point
            'wrap-iife': ['error', 'inside'],
            'yoda': ['error', 'never', { exceptRange: true }],

            // Strict Mode
            'strict': 'off', // not required with webpack

            // Variables
            'no-catch-shadow': 'error',
            'no-delete-var': 'error',
            'no-label-var': 'error',
            'no-shadow-restricted-names': 'error',
            'no-shadow': 'error',
            'no-undef-init': 'error',
            'no-undef': 'error',
            'no-undefined': 'off',
            'no-unused-vars': 'error',
            'no-use-before-define': 'error',

            // Stylistic Issues
            'array-bracket-spacing': ['error', 'never'],
            'block-spacing': 'error',
            'brace-style': ['error', '1tbs'],
            'camelcase': 'off',
            'comma-spacing': ['error', { before: false, after: true }],
            'comma-style': ['error', 'last'],
            'computed-property-spacing': ['error', 'never'],
            'consistent-this': ['error', 'that'],
            'eol-last': 'error',
            'func-names': 'off',
            'func-style': 'off',
            'indent': [
                'error',
                4,
                {
                    SwitchCase: 1
                }
            ],
            'key-spacing': ['error', { beforeColon: false, afterColon: true }],
            'linebreak-style': ['error', 'unix'],
            'max-nested-callbacks': ['error', 5],
            'new-cap': 'error',
            'new-parens': 'error',
            'newline-after-var': 'error',
            'no-array-constructor': 'error',
            'no-continue': 'error',
            'no-inline-comments': 'off',
            'no-lonely-if': 'error',
            'no-mixed-spaces-and-tabs': 'error',
            'no-multiple-empty-lines': ['error', { max: 2 }],
            'no-negated-condition': 'error',
            'no-nested-ternary': 'error',
            'no-new-object': 'error',
            'no-restricted-syntax': 'off',
            'no-ternary': 'off',
            'no-trailing-spaces': 'error',
            'no-underscore-dangle': 'off',
            'no-unneeded-ternary': 'error',
            'object-curly-spacing': [
                'error',
                'always',
                {
                    objectsInObjects: true,
                    arraysInObjects: true
                }
            ],
            'one-var': ['error', 'never'],
            'operator-assignment': 'error',
            'operator-linebreak': 'off',
            'padded-blocks': 'off',
            'quote-props': ['error', 'as-needed'],
            'quotes': ['error', 'single', 'avoid-escape'],
            'semi-spacing': ['error', { before: false, after: true }],
            'semi': ['error', 'always'],
            'sort-vars': 'off',
            'keyword-spacing': 'error',
            'space-before-blocks': 'error',
            // FIXME reenable after running prettier on full codebase
            'space-before-function-paren': ['off', { anonymous: 'never', named: 'never' }],
            'space-in-parens': ['error', 'never'],
            'space-infix-ops': 'error',
            'space-unary-ops': 'error',
            'spaced-comment': 'error',
            'wrap-regex': 'off',

            // ES6
            'arrow-parens': ['error', 'as-needed'],

            // Legacy
            'max-depth': ['error', 4],
            'max-len': ['error', 120],
            'max-params': ['error', 3],
            'max-statements': 'off',
            'no-bitwise': 'error',
            'no-plusplus': 'off',

            'compat/compat': 'error'
        }
    },
    {
        files: ['cms/tests/frontend/**/*.js'],
        rules: {
            'no-magic-numbers': 'off',
            'max-nested-callbacks': ['error', 8],
            'newline-after-var': 'off',
            'strict': 'off',
            'require-jsdoc': 'off'
        }
    }
];

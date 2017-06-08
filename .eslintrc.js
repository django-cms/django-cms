module.exports = {
    "env": {
        "browser": true,
        "node": true,
        "jquery": true,
        "jasmine": true,
        "es6": true
    },
    "globals": {
        "CMS": true,
        "Promise": true
    },
    "root": true,
    "ecmaFeatures": {
        "modules": true
    },
    "parser": "babel-eslint",
    "parserOptions": {
        "sourceType": "module"
    },
    "plugins": ["compat"],
    "settings": {
        "polyfills": [
            "document-currentscript"
        ]
    },
    "rules": {
        // Possible Errors
        "comma-dangle": [2, "never"],
        "no-cond-assign": 2,
        "no-console": 1,
        "no-constant-condition": 2,
        "no-control-regex": 2,
        "no-debugger": 2,
        "no-dupe-args": 2,
        "no-dupe-keys": 2,
        "no-duplicate-case": 2,
        "no-empty-character-class": 2,
        "no-empty": ["error", { "allowEmptyCatch": true }],
        "no-ex-assign": 2,
        "no-extra-boolean-cast": 2,
        "no-extra-parens": ["error", "all", {
            "nestedBinaryExpressions": false
        }],
        "no-extra-semi": 2,
        "no-func-assign": 2,
        "no-inner-declarations": 2,
        "no-invalid-regexp": 2,
        "no-irregular-whitespace": 2,
        "no-negated-in-lhs": 2,
        "no-obj-calls": 2,
        "no-regex-spaces": 2,
        "no-sparse-arrays": 2,
        "no-unexpected-multiline": 2,
        "no-unreachable": 2,
        "use-isnan": 2,
        "valid-jsdoc": [2, {
            "requireReturn": false,
            "requireParamDescription": false,
            "requireReturnDescription": false,
            "prefer": {
                "return": "returns"
            }
        }],
        "valid-typeof": 2,

        // Best Practices
        "accessor-pairs": 2,
        "block-scoped-var": 2,
        "complexity": ["error", { "max": 10 } ],
        "consistent-return": 0,
        "curly": 2,
        "default-case": 2,
        "dot-location": [2, "property"],
        "dot-notation": 2,
        "eqeqeq": 2,
        "guard-for-in": 2,
        "no-alert": 2,
        "no-caller": 2,
        "no-case-declarations": 2,
        "no-div-regex": 2,
        "no-else-return": 1,
        "no-empty-pattern": 2,
        "no-eq-null": 2,
        "no-eval": 2,
        "no-extend-native": 2,
        "no-extra-bind": 2,
        "no-fallthrough": 2,
        "no-floating-decimal": 2,
        "no-implicit-coercion": 0,
        "no-implied-eval": 2,
        "no-invalid-this": 0,
        "no-iterator": 2,
        "no-labels": 2,
        "no-lone-blocks": 2,
        "no-loop-func": 2,
        "no-magic-numbers": [
            "error", {
                "ignore": [0, -1, 1, 2],
                "ignoreArrayIndexes": true
            }
        ],
        "no-multi-spaces": 2,
        "no-multi-str": 0,
        "no-native-reassign": 2,
        "no-new-func": 2,
        "no-new-wrappers": 2,
        "no-new": 0,
        "no-octal-escape": 2,
        "no-octal": 2,
        "no-param-reassign": 2,
        "no-process-env": 0,
        "no-proto": 2,
        "no-redeclare": 2,
        "no-return-assign": 2,
        "no-script-url": 2,
        "no-self-compare": 2,
        "no-sequences": 2,
        "no-throw-literal": 2,
        "no-unused-expressions": [2, { "allowShortCircuit": true }],
        "no-useless-call": 2,
        "no-useless-concat": 2,
        "no-void": 2,
        "no-warning-comments": 0,
        "no-with": 2,
        "radix": 2,
        "vars-on-top": 0, // FIXME should be enabled at some point
        "wrap-iife": [2, "inside"],
        "yoda": [2, "never", { "exceptRange": true }],

        // Strict Mode
        "strict": 0, // not required with webpack

        // Variables
        "init-declarations": 0,
        "no-catch-shadow": 2,
        "no-delete-var": 2,
        "no-label-var": 2,
        "no-shadow-restricted-names": 2,
        "no-shadow": 2,
        "no-undef-init": 2,
        "no-undef": 2,
        "no-undefined": 0,
        "no-unused-vars": 2,
        "no-use-before-define": 2,

        // Stylistic Issues
        "array-bracket-spacing": [2, "never"],
        "block-spacing": 2,
        "brace-style": [2, "1tbs"],
        "camelcase": 0,
        "comma-spacing": [2, {"before": false, "after": true}],
        "comma-style": [2, "last"],
        "computed-property-spacing": [2, "never"],
        "consistent-this": [2, "that"],
        "eol-last": 2,
        "func-names": 0,
        "func-style": 0,
        "id-length": 0,
        "id-match": 0,
        "indent": ["error", 4, {
            "SwitchCase": 1
        }],
        "jsx-quotes": 0,
        "key-spacing": [2, {"beforeColon": false, "afterColon": true}],
        "linebreak-style": [2, "unix"],
        "lines-around-comment": 0,
        "max-nested-callbacks": [2, 5],
        "new-cap": 2,
        "new-parens": 2,
        "newline-after-var": 2,
        "no-array-constructor": 2,
        "no-continue": 2,
        "no-inline-comments": 0,
        "no-lonely-if": 2,
        "no-mixed-spaces-and-tabs": 2,
        "no-multiple-empty-lines": [2, {"max": 2}],
        "no-negated-condition": 2,
        "no-nested-ternary": 2,
        "no-new-object": 2,
        "no-restricted-syntax": 0,
        "no-spaced-func": 0,
        "no-ternary": 0,
        "no-trailing-spaces": 2,
        "no-underscore-dangle": 0,
        "no-unneeded-ternary": 2,
        "object-curly-spacing": [2, "always", {
            "objectsInObjects": true,
            "arraysInObjects": true
        }],
        "one-var": [2, "never"],
        "operator-assignment": 2,
        "operator-linebreak": [2, "after"],
        "padded-blocks": 0,
        "quote-props": [2, "consistent-as-needed"],
        "quotes": [2, "single", "avoid-escape"],
        "require-jsdoc": 2,
        "semi-spacing": [2, {"before": false, "after": true}],
        "semi": [2, "always"],
        "sort-vars": 0,
        "keyword-spacing": 2,
        "space-before-blocks": 2,
        // FIXME reenable after running prettier on full codebase
        "space-before-function-paren": [0, { "anonymous": "never", "named": "never" }],
        "space-in-parens": [2, "never"],
        "space-infix-ops": 2,
        "space-unary-ops": 2,
        "spaced-comment": 2,
        "wrap-regex": 2,

        // ES6
        "arrow-parens": [2, "as-needed"],

        // Legacy
        "max-depth": [2, 4],
        "max-len": [2, 120],
        "max-params": [2, 3],
        "max-statements": 0,
        "no-bitwise": 2,
        "no-plusplus": 0,

        "compat/compat": 2
    }
}

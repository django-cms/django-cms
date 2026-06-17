/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// NAMESPACES
/**
 * @module CMS
 */
var CMS = window.CMS || {};

document.addEventListener('DOMContentLoaded', function() {
    /**
     * Adds internal methods for the creation wizard.
     *
     * @class Wizards
     * @namespace CMS
     */
    'use strict';

    CMS.Wizards = {
        _choice: function initialize() {
            // set active element when making a choice
            const form = document.querySelector('form');
            const choices = document.querySelectorAll('.choice');

            if (!form || !choices.length) {
                return;
            }

            /**
             * Mark a choice as the selected radio of the group, keeping the
             * ARIA state, the roving tabindex and the backing <input> in sync.
             *
             * @param {HTMLElement} choice the choice element to activate
             * @param {Boolean} setFocus whether to move focus to the choice
             */
            function activate(choice, setFocus) {
                var i;
                var radio;

                for (i = 0; i < choices.length; i++) {
                    choices[i].classList.remove('active');
                    choices[i].setAttribute('aria-checked', 'false');
                    choices[i].setAttribute('tabindex', '-1');
                    radio = choices[i].querySelector('input[type="radio"]');
                    if (radio) {
                        radio.checked = false;
                    }
                }

                choice.classList.add('active');
                choice.setAttribute('aria-checked', 'true');
                choice.setAttribute('tabindex', '0');
                radio = choice.querySelector('input[type="radio"]');
                if (radio) {
                    radio.checked = true;
                }

                if (setFocus) {
                    choice.focus();
                }
            }

            choices.forEach(function(choice) {
                choice.addEventListener('click', function() {
                    activate(choice, false);
                });

                choice.addEventListener('keydown', function(e) {
                    var index = Array.prototype.indexOf.call(choices, choice);

                    switch (e.keyCode) {
                        case CMS.KEYS.ENTER:
                            e.preventDefault();
                            activate(choice, false);
                            form.submit();
                            break;
                        case CMS.KEYS.SPACE:
                            e.preventDefault();
                            activate(choice, false);
                            break;
                        case CMS.KEYS.UP:
                        case CMS.KEYS.LEFT:
                            e.preventDefault();
                            activate(
                                choices[(index - 1 + choices.length) % choices.length],
                                true
                            );
                            break;
                        case CMS.KEYS.DOWN:
                        case CMS.KEYS.RIGHT:
                            e.preventDefault();
                            activate(
                                choices[(index + 1) % choices.length],
                                true
                            );
                            break;
                        default:
                            break;
                    }
                });

                // submit the form on double click
                choice.addEventListener('dblclick', function() {
                    activate(choice, false);
                    form.submit();
                });
            });

            // make sure the active (or first) choice is the tab stop and
            // focus it so hitting "enter" doesn't trigger a refresh
            const active = document.querySelector('.choice.active');

            activate(active || choices[0], true);
        }
    };

    // directly initialize required methods
    if (document.querySelector('.choice')) {
        CMS.Wizards._choice();
    }
});

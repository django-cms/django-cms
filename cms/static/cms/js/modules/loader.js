import Nprogress from 'nprogress';
import { debounce } from 'lodash';

Nprogress.configure({
    showSpinner: false,
    parent: '#cms-top',
    trickleSpeed: 200,
    minimum: 0.3,
    template: `
        <div class="cms-loading-bar" role="bar">
            <div class="cms-loading-peg"></div>
        </div>
    `
});

/**
 * Shows the loader spinner on the trigger knob for the toolbar.
 *
 * @method showLoader
 */
// instanbul ignore next
export const showLoader = debounce(() => {
    // due to this being animated loader we don't want things that show and hide loader
    // in one frame to actually show it, for example when setSettings is called in a browser
    // that supports localStorage. (it happens every time you click on a plugin for example)
    // we want to debounce the call and cancel it if it's in the same frame
    Nprogress.start();
}, 0);

/**
 * Hides the loader spinner on the trigger knob for the toolbar.
 *
 * @method hideLoader
 */
// instanbul ignore next
export const hideLoader = () => {
    showLoader.cancel();
    Nprogress.done();
};

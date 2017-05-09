import initHelpModal from './help';
import $ from 'jquery';
import initFocusPlaceholders from './placeholders';
import initCreateModal from './create-modal';
import initFocusToolbar from './toolbar';

// eslint-disable-next-line require-jsdoc
export default function () {
    // istanbul ignore next
    $(function () {
        initHelpModal();
        initFocusPlaceholders();
        initCreateModal();
        initFocusToolbar();
    });
}

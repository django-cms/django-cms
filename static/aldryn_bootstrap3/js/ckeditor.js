/*
 * Copyright https://github.com/divio/django-cms
 */

// #############################################################################
// CKEDITOR
/**
 * Default CKEDITOR Styles
 * Added within src/settings.py CKEDITOR_SETTINGS.stylesSet
 * http://getbootstrap.com/css/#type
 *
 * @module CKEDITOR
 */
/* global CKEDITOR */

CKEDITOR.allElements = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'];
CKEDITOR.stylesSet.add('default', [
    { name: 'Text lead', element: CKEDITOR.allElements, attributes: { class: 'lead' }},

    { name: 'Text left', element: CKEDITOR.allElements, attributes: { class: 'text-left' }},
    { name: 'Text center', element: CKEDITOR.allElements, attributes: { class: 'text-center' }},
    { name: 'Text right', element: CKEDITOR.allElements, attributes: { class: 'text-right' }},
    { name: 'Text kustify', element: CKEDITOR.allElements, attributes: { class: 'text-justify' }},
    { name: 'Text no wrap', element: CKEDITOR.allElements, attributes: { class: 'text-nowrap' }},

    { name: 'Abbr initialism', element: 'abbr', attributes: { class: 'initialism' }},

    { name: 'List unstyled', element: ['ul', 'ol'], attributes: { class: 'list-unstyled' }},
    { name: 'List inline', element: ['ul', 'ol'], attributes: { class: 'list-inline' }},
    { name: 'Horizontal description', element: 'dl', attributes: { class: 'dl-horizontal' }},

    { name: 'Table', element: 'table', attributes: { class: 'table' }},
    { name: 'Table striped', element: 'table', attributes: { class: 'table-striped' }},
    { name: 'Table bordered', element: 'table', attributes: { class: 'table-bordered' }},
    { name: 'Table hover', element: 'table', attributes: { class: 'table-hover' }},
    { name: 'Table condensed', element: 'table', attributes: { class: 'table-condensed' }},
    { name: 'Table responsive', element: 'table', attributes: { class: 'table-responsive' }},

    { name: 'Table cell active', element: ['tr', 'th', 'td'], attributes: { class: 'active' }},
    { name: 'Table cell success', element: ['tr', 'th', 'td'], attributes: { class: 'success' }},
    { name: 'Table cell info', element: ['tr', 'th', 'td'], attributes: { class: 'info' }},
    { name: 'Table cell warning', element: ['tr', 'th', 'td'], attributes: { class: 'warning' }},
    { name: 'Table cell danger', element: ['tr', 'th', 'td'], attributes: { class: 'danger' }},

    { name: 'Text primary', element: 'span', attributes: { class: 'text-primary' }},
    { name: 'Text success', element: 'span', attributes: { class: 'text-success' }},
    { name: 'Text info', element: 'span', attributes: { class: 'text-info' }},
    { name: 'Text warning', element: 'span', attributes: { class: 'text-warning' }},
    { name: 'Text danger', element: 'span', attributes: { class: 'text-danger' }},
    { name: 'Text muted', element: 'span', attributes: { class: 'text-muted' }},

    { name: 'Image responsive', element: 'img', attributes: { class: 'img-responsive' }},
    { name: 'Image rounded', element: 'img', attributes: { class: 'img-rounded' }},
    { name: 'Image circle', element: 'img', attributes: { class: 'img-circle' }},
    { name: 'Image thumbnail', element: 'img', attributes: { class: 'img-thumbnail' }},

    { name: 'Blockquote reverse', element: 'blockquote', attributes: { class: 'blockquote-reverse' }},

    { name: 'Background primary', element: CKEDITOR.allElements, attributes: { class: 'bg-primary' }},
    { name: 'Background success', element: CKEDITOR.allElements, attributes: { class: 'bg-success' }},
    { name: 'Background info', element: CKEDITOR.allElements, attributes: { class: 'bg-info' }},
    { name: 'Background warning', element: CKEDITOR.allElements, attributes: { class: 'bg-warning' }},
    { name: 'Background danger', element: CKEDITOR.allElements, attributes: { class: 'bg-danger' }},

    { name: 'Pull left', element: CKEDITOR.allElements, attributes: { class: 'pull-left' }},
    { name: 'Pull right', element: CKEDITOR.allElements, attributes: { class: 'pull-right' }},
    { name: 'Center block', element: CKEDITOR.allElements, attributes: { class: 'center-block' }},
    { name: 'Clearfix', element: CKEDITOR.allElements, attributes: { class: 'clearfix' }},

    { name: 'Screenreader only', element: CKEDITOR.allElements, attributes: { class: 'sr-only' }},
    { name: 'Screenreader only focusable', element: CKEDITOR.allElements, attributes: { class: 'sr-only-focusable' }},
    { name: 'Text hide', element: CKEDITOR.allElements, attributes: { class: 'text-hide' }},

    // not enabled by default
    // http://getbootstrap.com/css/#helper-classes-close
    // { name: 'Close', element: CKEDITOR.allElements, attributes: { class: 'center-block' }},
    // http://getbootstrap.com/css/#helper-classes-carets
    // { name: 'Caret', element: CKEDITOR.allElements, attributes: { class: 'clearfix' }},

    // additional classes not included in basic bootstrap
    { name: 'Spacer', element: 'div', attributes: { class: 'spacer' }},
    { name: 'Spacer Small', element: 'div', attributes: { class: 'spacer-xs' }},
    { name: 'Spacer Large', element: 'div', attributes: { class: 'spacer-lg' }},
    { name: 'Spacer Zero', element: 'div', attributes: { class: 'spacer-zero' }}
]);

/*
 * Extend ckeditor default settings
 * DOCS: http://docs.ckeditor.com/#!/api/CKEDITOR.dtd
 */
CKEDITOR.dtd.$removeEmpty.span = 0;

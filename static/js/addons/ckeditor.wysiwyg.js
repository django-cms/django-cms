/*
 * Copyright (c) 2013, Divio AG
 * Licensed under BSD
 * http://github.com/divio/djangocms-boilerplate-webpack
 */

// #############################################################################
// CKEDITOR
/**
 * Default CKEDITOR Styles
 * Added within src/settings.py CKEDITOR_SETTINGS.stylesSet
 *
 * @module CKEDITOR
 */
/* global CKEDITOR */

CKEDITOR.allElements = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div'];
CKEDITOR.stylesSet.add('default', [
    /* Block Styles */
    { name: 'Text Lead', element: CKEDITOR.allElements, attributes: { class: 'lead' }},

    { name: 'Text Left', element: CKEDITOR.allElements, attributes: { class: 'text-left' }},
    { name: 'Text Center', element: CKEDITOR.allElements, attributes: { class: 'text-center' }},
    { name: 'Text Right', element: CKEDITOR.allElements, attributes: { class: 'text-right' }},
    { name: 'Text Justify', element: CKEDITOR.allElements, attributes: { class: 'text-justify' }},
    { name: 'Text NoWrap', element: CKEDITOR.allElements, attributes: { class: 'text-nowrap' }},

    { name: 'Spacer', element: 'div', attributes: { class: 'spacer' }},
    { name: 'Spacer Small', element: 'div', attributes: { class: 'spacer-xs' }},
    { name: 'Spacer Large', element: 'div', attributes: { class: 'spacer-lg' }},
    { name: 'Spacer Zero', element: 'div', attributes: { class: 'spacer-zero' }},

    { name: 'List Unstyled', element: ['ul', 'ol'], attributes: { class: 'list-unstyled' }},
    { name: 'List Inline', element: ['ul', 'ol'], attributes: { class: 'list-inline' }},
    { name: 'Horizontal Description', element: 'dl', attributes: { class: 'dl-horizontal' }},

    { name: 'Table', element: 'table', attributes: { class: 'table' }},
    { name: 'Table Responsive', element: 'table', attributes: { class: 'table-responsive' }},
    { name: 'Table Striped', element: 'table', attributes: { class: 'table-striped' }},
    { name: 'Table Bordered', element: 'table', attributes: { class: 'table-bordered' }},
    { name: 'Table Hover', element: 'table', attributes: { class: 'table-hover' }},
    { name: 'Table Condensed', element: 'table', attributes: { class: 'table-condensed' }},

    { name: 'Table Cell Active', element: ['tr', 'th', 'td'], attributes: { class: 'active' }},
    { name: 'Table Cell Success', element: ['tr', 'th', 'td'], attributes: { class: 'success' }},
    { name: 'Table Cell Warning', element: ['tr', 'th', 'td'], attributes: { class: 'warning' }},
    { name: 'Table Cell Danger', element: ['tr', 'th', 'td'], attributes: { class: 'danger' }},
    { name: 'Table Cell Info', element: ['tr', 'th', 'td'], attributes: { class: 'info' }},

    /* Inline Styles */
    { name: 'Text Primary', element: 'span', attributes: { class: 'text-primary' }},
    { name: 'Text Success', element: 'span', attributes: { class: 'text-success' }},
    { name: 'Text Info', element: 'span', attributes: { class: 'text-info' }},
    { name: 'Text Warning', element: 'span', attributes: { class: 'text-warning' }},
    { name: 'Text Danger', element: 'span', attributes: { class: 'text-danger' }},
    { name: 'Text Muted', element: 'span', attributes: { class: 'text-muted' }},

    { name: 'Image Responsive', element: 'img', attributes: { class: 'img-responsive' }},
    { name: 'Image Rounded', element: 'img', attributes: { class: 'img-rounded' }},
    { name: 'Image Circle', element: 'img', attributes: { class: 'img-circle' }},
    { name: 'Image Thumbnail', element: 'img', attributes: { class: 'img-thumbnail' }},

    { name: 'Pull Left', element: CKEDITOR.allElements, attributes: { class: 'pull-left' }},
    { name: 'Pull Right', element: CKEDITOR.allElements, attributes: { class: 'pull-right' }},

    { name: 'Blockquote Reverse', element: 'blockquote', attributes: { class: 'blockquote-reverse' }},
]);

/*
 * Extend ckeditor default settings
 * DOCS: http://docs.ckeditor.com/#!/api/CKEDITOR.dtd
 */
CKEDITOR.dtd.$removeEmpty.span = 0;

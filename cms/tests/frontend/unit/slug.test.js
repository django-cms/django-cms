'use strict';
var $ = require('jquery');
var addSlugHandlers = require('../../../static/cms/js/modules/slug').default;

describe('addSlugHandlers', function() {
    var container;
    var title;
    var slug;

    /**
     * Types into an input the way a user would - the value is set and an "input"
     * event is dispatched, which is what the handlers listen to.
     *
     * @function type
     * @param {jQuery} input the field to type into
     * @param {String} value the new value
     * @returns {void}
     */
    function type(input, value) {
        input.val(value);
        input.trigger('input');
    }

    /**
     * Simulates leaving a field after having edited it.
     *
     * @function blur
     * @param {jQuery} input the field to blur
     * @returns {void}
     */
    function blur(input) {
        input.trigger('change');
    }

    beforeEach(function() {
        container = document.createElement('div');
        container.innerHTML = '<input id="id_title"><input id="id_slug">';
        document.body.appendChild(container);
        title = $(container).find('#id_title');
        slug = $(container).find('#id_slug');

        window.URLify = jasmine.createSpy('URLify').and.callFake(function(value) {
            return value
                .toLowerCase()
                .trim()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/^-|-$/g, '');
        });
    });

    afterEach(function() {
        document.body.removeChild(container);
        delete window.UNIHANDECODER;
        window.URLify = undefined;
    });

    it('does not fail if there is no slug or no title field', function() {
        expect(function() {
            addSlugHandlers(title, null);
        }).not.toThrow();
        expect(function() {
            addSlugHandlers(null, slug);
        }).not.toThrow();
        expect(function() {
            addSlugHandlers(title, $('#does-not-exist'));
        }).not.toThrow();
    });

    it('generates the slug from the title while the slug is empty', function() {
        addSlugHandlers(title, slug);

        type(title, 'I AM A TILE');

        expect(slug.val()).toEqual('i-am-a-tile');
    });

    it('keeps a manually entered slug when the title changes', function() {
        addSlugHandlers(title, slug);

        type(title, 'I AM A TILE');
        expect(slug.val()).toEqual('i-am-a-tile');

        type(slug, 'some-page');
        blur(slug);

        type(title, 'I AM A TITLE');

        expect(slug.val()).toEqual('some-page');
    });

    it('resumes generating the slug once the user empties it', function() {
        addSlugHandlers(title, slug);

        type(slug, 'some-page');
        type(title, 'I AM A TILE');
        expect(slug.val()).toEqual('some-page');

        type(slug, '');
        type(title, 'I AM A TITLE');

        expect(slug.val()).toEqual('i-am-a-title');
    });

    it('does not touch a slug that already has a value', function() {
        slug.val('existing-page');

        addSlugHandlers(title, slug);
        type(title, 'New title');

        expect(slug.val()).toEqual('existing-page');
    });

    it('does not bind twice if called again for the same field', function() {
        addSlugHandlers(title, slug);
        addSlugHandlers(title, slug);

        window.URLify.calls.reset();
        type(title, 'Title');

        // a second set of handlers would generate the slug twice per keystroke
        expect(window.URLify).toHaveBeenCalledTimes(1);
    });

    it('does not bind if django admin prepopulates the field', function() {
        var constants = document.createElement('span');

        constants.id = 'django-admin-prepopulated-fields-constants';
        constants.dataset.prepopulatedFields = JSON.stringify([{ id: '#id_slug' }]);
        container.appendChild(constants);

        addSlugHandlers(title, slug);
        type(title, 'Title');

        expect(slug.val()).toEqual('');
        container.removeChild(constants);
    });

    it('marks title and slug as changed when they are edited', function() {
        addSlugHandlers(title, slug);

        expect(slug.data('changed')).toBeUndefined();

        blur(title);
        blur(slug);

        expect(title.data('changed')).toEqual(true);
        expect(slug.data('changed')).toEqual(true);
    });

    it('does not mark an auto-generated slug as changed', function() {
        addSlugHandlers(title, slug);

        type(title, 'Some title');
        blur(title);

        expect(slug.val()).toEqual('some-title');
        expect(slug.data('changed')).toBeUndefined();
    });

    it('uses the unihandecoder if available', function() {
        window.UNIHANDECODER = { decode: jasmine.createSpy('decode').and.returnValue('decoded') };

        addSlugHandlers(title, slug);
        type(title, '日本語');

        expect(window.UNIHANDECODER.decode).toHaveBeenCalledWith('日本語');
        expect(slug.val()).toEqual('decoded');
    });
});

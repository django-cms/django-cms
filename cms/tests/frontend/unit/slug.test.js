'use strict';
const addSlugHandlers = require('../../../static/cms/js/modules/slug').default;

describe('addSlugHandlers', () => {
    let container;
    let title;
    let slug;

    /**
     * Types into an input the way a user would - the value is set and an "input"
     * event is dispatched, which is what the handlers listen to.
     */
    const type = (input, value) => {
        input.value = value;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    };

    const blur = input => input.dispatchEvent(new Event('change', { bubbles: true }));

    beforeEach(() => {
        container = document.createElement('div');
        container.innerHTML = '<input id="id_title"><input id="id_slug">';
        document.body.appendChild(container);
        title = container.querySelector('#id_title');
        slug = container.querySelector('#id_slug');
    });

    afterEach(() => {
        document.body.removeChild(container);
        delete window.UNIHANDECODER;
        window.URLify = undefined;
    });

    beforeEach(() => {
        window.URLify = jasmine.createSpy('URLify').and.callFake(
            value => value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
        );
    });

    it('does not fail if there is no slug or no title field', () => {
        expect(() => addSlugHandlers(title, null)).not.toThrow();
        expect(() => addSlugHandlers(null, slug)).not.toThrow();
    });

    it('generates the slug from the title while the slug is empty', () => {
        addSlugHandlers(title, slug);

        type(title, 'I AM A TILE');

        expect(slug.value).toEqual('i-am-a-tile');
    });

    it('keeps a manually entered slug when the title changes', () => {
        addSlugHandlers(title, slug);

        type(title, 'I AM A TILE');
        expect(slug.value).toEqual('i-am-a-tile');

        type(slug, 'some-page');
        blur(slug);

        type(title, 'I AM A TITLE');

        expect(slug.value).toEqual('some-page');
    });

    it('resumes generating the slug once the user empties it', () => {
        addSlugHandlers(title, slug);

        type(slug, 'some-page');
        type(title, 'I AM A TILE');
        expect(slug.value).toEqual('some-page');

        type(slug, '');
        type(title, 'I AM A TITLE');

        expect(slug.value).toEqual('i-am-a-title');
    });

    it('does not touch a slug that already has a value', () => {
        slug.value = 'existing-page';

        addSlugHandlers(title, slug);
        type(title, 'New title');

        expect(slug.value).toEqual('existing-page');
    });

    it('does not bind twice if called again for the same field', () => {
        addSlugHandlers(title, slug);
        addSlugHandlers(title, slug);

        window.URLify.calls.reset();
        type(title, 'Title');

        // a second set of handlers would generate the slug twice per keystroke
        expect(window.URLify).toHaveBeenCalledTimes(1);
    });

    it('does not bind if django admin prepopulates the field', () => {
        const constants = document.createElement('span');

        constants.id = 'django-admin-prepopulated-fields-constants';
        constants.dataset.prepopulatedFields = JSON.stringify([{ id: '#id_slug' }]);
        container.appendChild(constants);

        addSlugHandlers(title, slug);
        type(title, 'Title');

        expect(slug.value).toEqual('');
        container.removeChild(constants);
    });

    it('marks title and slug as changed when they are edited', () => {
        addSlugHandlers(title, slug);

        expect(slug.dataset.changed).toBeUndefined();

        blur(title);
        blur(slug);

        expect(title.dataset.changed).toEqual('true');
        expect(slug.dataset.changed).toEqual('true');
    });

    it('does not mark an auto-generated slug as changed', () => {
        addSlugHandlers(title, slug);

        type(title, 'Some title');
        blur(title);

        expect(slug.value).toEqual('some-title');
        expect(slug.dataset.changed).toBeUndefined();
    });

    it('uses the unihandecoder if available', () => {
        window.UNIHANDECODER = { decode: jasmine.createSpy('decode').and.returnValue('decoded') };

        addSlugHandlers(title, slug);
        type(title, '日本語');

        expect(window.UNIHANDECODER.decode).toHaveBeenCalledWith('日本語');
        expect(slug.value).toEqual('decoded');
    });
});

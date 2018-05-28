'use strict';
const preloadImagesFromMarkup = require('../../../static/cms/js/modules/preload-images').default;

describe('preloadImagesFromMarkup', () => {
    let preload;

    beforeEach(() => {
        preload = jasmine.createSpy();
        preloadImagesFromMarkup.__Rewire__('preload', preload);
    });

    afterEach(() => {
        preloadImagesFromMarkup.__ResetDependency__('preload');
    });

    const tests = [
        {
            input: 'no img',
            expected: []
        },
        {
            input: '<img src="whatever">',
            expected: ['whatever']
        },
        {
            input: "<img src='whatever'>",
            expected: ['whatever']
        },
        {
            input: `<img
            src="whatever"
            class="x" other attributes />`,
            expected: ['whatever']
        },
        {
            input: `
            <img src="/static/img1.png">
            <img src="/static/img2.png">
            `,
            expected: [
                '/static/img1.png',
                '/static/img2.png'
            ]
        },
        {
            input: '<IMG CLASS="WUT" src="/static/img1.jpg?2" />',
            expected: [
                '/static/img1.jpg?2'
            ]
        }
    ];

    tests.forEach((test, i) => {
        it(`preloads images from markup ${i}`, () => {
            preloadImagesFromMarkup(test.input);

            expect(preload).toHaveBeenCalledTimes(test.expected.length);
            test.expected.forEach(ex => expect(preload).toHaveBeenCalledWith(ex));
        });
    });
});

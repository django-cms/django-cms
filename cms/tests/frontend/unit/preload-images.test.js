'use strict';
import preloadImagesFromMarkup from '../../../static/cms/js/modules/preload-images';
describe('preloadImagesFromMarkup', () => {
    let preloaded;
    let OriginalImage;

    // preload() is module private, so the images it creates are what we observe
    beforeEach(() => {
        preloaded = [];
        OriginalImage = window.Image;
        window.Image = function FakeImage() {
            const image = {};

            let src;

            Object.defineProperty(image, 'src', {
                get() {
                    return src;
                },
                set(value) {
                    src = value;
                    preloaded.push(value);
                }
            });
            return image;
        };
    });

    afterEach(() => {
        window.Image = OriginalImage;
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

            expect(preloaded.length).toEqual(test.expected.length);
            test.expected.forEach(ex => expect(preloaded).toContain(ex));
        });
    });
});

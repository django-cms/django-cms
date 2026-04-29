import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { preloadImagesFromMarkup } from '../../frontend/modules/structureboard/network/images';

describe('network/images — preloadImagesFromMarkup', () => {
    let imagesCreated: string[];
    const OriginalImage = global.Image;

    beforeEach(() => {
        imagesCreated = [];
        // Stub Image constructor to capture src writes.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (global as any).Image = vi.fn(function FakeImage(this: { src: string }) {
            const self = this;
            Object.defineProperty(self, 'src', {
                set(value: string) {
                    imagesCreated.push(value);
                },
                get() {
                    return '';
                },
            });
        });
    });
    afterEach(() => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (global as any).Image = OriginalImage;
    });

    it('preloads every <img src> URL', () => {
        preloadImagesFromMarkup(`
            <img src="/a.png">
            <p>some text</p>
            <img class="x" src='/b.jpg'>
            <img alt="x" src="https://example.com/c.gif" />
        `);
        expect(imagesCreated).toEqual([
            '/a.png',
            '/b.jpg',
            'https://example.com/c.gif',
        ]);
    });

    it('handles empty / missing input', () => {
        preloadImagesFromMarkup('');
        expect(imagesCreated).toEqual([]);
    });

    it('handles markup with no img tags', () => {
        preloadImagesFromMarkup('<div><p>nothing</p></div>');
        expect(imagesCreated).toEqual([]);
    });

    it('repeat calls do not interfere with each other (regex.lastIndex reset)', () => {
        preloadImagesFromMarkup('<img src="/first.png">');
        preloadImagesFromMarkup('<img src="/second.png">');
        expect(imagesCreated).toEqual(['/first.png', '/second.png']);
    });
});

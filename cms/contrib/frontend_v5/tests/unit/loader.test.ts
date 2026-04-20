import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { showLoader, hideLoader } from '../../frontend/modules/loader';

describe('loader', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="cms-top"></div>';
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
        document.body.innerHTML = '';
    });

    it('showLoader creates the loading bar inside #cms-top after a tick', () => {
        showLoader();
        expect(document.getElementById('cms-loading-bar')).toBeNull();

        vi.advanceTimersByTime(0);
        const bar = document.getElementById('cms-loading-bar');
        expect(bar).not.toBeNull();
        expect(bar?.parentElement?.id).toBe('cms-top');
        expect(bar?.classList.contains('cms-loading-bar')).toBe(true);
    });

    it('showLoader is idempotent — second call does not create a duplicate', () => {
        showLoader();
        vi.advanceTimersByTime(0);
        showLoader();
        vi.advanceTimersByTime(0);
        expect(document.querySelectorAll('#cms-loading-bar')).toHaveLength(1);
    });

    it('showLoader is a no-op when #cms-top is absent', () => {
        document.body.innerHTML = '';
        showLoader();
        vi.advanceTimersByTime(0);
        expect(document.getElementById('cms-loading-bar')).toBeNull();
    });

    it('hideLoader fades out and removes the bar', () => {
        showLoader();
        vi.advanceTimersByTime(0);
        expect(document.getElementById('cms-loading-bar')).not.toBeNull();

        hideLoader();
        const bar = document.getElementById('cms-loading-bar');
        expect(bar?.style.opacity).toBe('0');

        vi.advanceTimersByTime(300);
        expect(document.getElementById('cms-loading-bar')).toBeNull();
    });

    it('hideLoader cancels a pending showLoader (no flicker)', () => {
        showLoader();
        hideLoader();
        vi.advanceTimersByTime(0);
        expect(document.getElementById('cms-loading-bar')).toBeNull();
    });

    it('hideLoader is safe when no bar exists', () => {
        expect(() => hideLoader()).not.toThrow();
    });
});

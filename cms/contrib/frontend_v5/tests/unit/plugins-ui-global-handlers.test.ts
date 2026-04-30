import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import {
    _resetGlobalHandlersForTest,
    initializeGlobalHandlers,
    isExpandMode,
    setExpandMode,
} from '../../frontend/modules/plugins/ui/global-handlers';

describe('global-handlers — expand-mode flag', () => {
    afterEach(() => {
        _resetGlobalHandlersForTest();
    });

    it('setExpandMode + isExpandMode round-trip', () => {
        expect(isExpandMode()).toBe(false);
        setExpandMode(true);
        expect(isExpandMode()).toBe(true);
        setExpandMode(false);
        expect(isExpandMode()).toBe(false);
    });
});

describe('global-handlers — initializeGlobalHandlers', () => {
    beforeEach(() => {
        _resetGlobalHandlersForTest();
    });
    afterEach(() => {
        _resetGlobalHandlersForTest();
        document.body.innerHTML = '';
    });

    it('shift keydown sets expandmode, keyup clears it', () => {
        initializeGlobalHandlers();
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Shift' }));
        expect(isExpandMode()).toBe(true);
        document.dispatchEvent(new KeyboardEvent('keyup', { key: 'Shift' }));
        expect(isExpandMode()).toBe(false);
    });

    it('non-shift keys do not flip the flag', () => {
        initializeGlobalHandlers();
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' }));
        expect(isExpandMode()).toBe(false);
    });

    it('window blur clears the flag', () => {
        initializeGlobalHandlers();
        setExpandMode(true);
        window.dispatchEvent(new Event('blur'));
        expect(isExpandMode()).toBe(false);
    });

    it('static-dragarea click toggles cms-dragarea-static-expanded', () => {
        document.body.innerHTML = `
            <div class="cms-dragarea cms-dragarea-static">
                <div class="cms-dragbar"><span>title</span></div>
            </div>
        `;
        initializeGlobalHandlers();
        const dragbar = document.querySelector('.cms-dragbar') as HTMLElement;
        const dragarea = document.querySelector('.cms-dragarea') as HTMLElement;
        dragbar.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(dragarea.classList.contains('cms-dragarea-static-expanded')).toBe(true);
        dragbar.dispatchEvent(new MouseEvent('click', { bubbles: true }));
        expect(dragarea.classList.contains('cms-dragarea-static-expanded')).toBe(false);
    });

    it('is idempotent — calling twice does not re-bind shift handler twice', () => {
        initializeGlobalHandlers();
        initializeGlobalHandlers();
        // Without re-binding, a single keydown still flips the flag.
        document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Shift' }));
        expect(isExpandMode()).toBe(true);
    });
});

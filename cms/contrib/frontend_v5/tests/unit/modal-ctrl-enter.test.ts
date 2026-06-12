import { afterEach, describe, expect, it, vi } from 'vitest';
import { setupCtrlEnterSave } from '../../frontend/modules/modal/ctrl-enter';

afterEach(() => {
    document.body.innerHTML = '';
    vi.unstubAllGlobals();
});

function setupDom(): HTMLElement {
    document.body.innerHTML = `
        <div class="cms-modal-buttons">
            <a class="cms-btn cms-btn-action" href="#">Save</a>
        </div>
    `;
    return document.querySelector<HTMLElement>('.cms-btn-action')!;
}

describe('setupCtrlEnterSave', () => {
    it('Ctrl-Enter clicks the default action button on non-Mac', () => {
        Object.defineProperty(navigator, 'platform', {
            configurable: true,
            value: 'Linux x86_64',
        });
        const btn = setupDom();
        const click = vi.fn();
        btn.addEventListener('click', click);
        const handle = setupCtrlEnterSave(document);
        document.dispatchEvent(
            new KeyboardEvent('keydown', {
                ctrlKey: true,
                key: 'Enter',
                keyCode: 13,
            }),
        );
        expect(click).toHaveBeenCalledOnce();
        handle.destroy();
    });

    it('Cmd-Enter clicks the default action button on Mac', () => {
        Object.defineProperty(navigator, 'platform', {
            configurable: true,
            value: 'MacIntel',
        });
        const btn = setupDom();
        const click = vi.fn();
        btn.addEventListener('click', click);
        const handle = setupCtrlEnterSave(document);
        document.dispatchEvent(
            new KeyboardEvent('keydown', {
                metaKey: true,
                key: 'Enter',
                keyCode: 13,
            }),
        );
        expect(click).toHaveBeenCalled();
        handle.destroy();
    });

    it('destroy() detaches the handler', () => {
        Object.defineProperty(navigator, 'platform', {
            configurable: true,
            value: 'Linux x86_64',
        });
        const btn = setupDom();
        const click = vi.fn();
        btn.addEventListener('click', click);
        const handle = setupCtrlEnterSave(document);
        handle.destroy();
        document.dispatchEvent(
            new KeyboardEvent('keydown', {
                ctrlKey: true,
                key: 'Enter',
                keyCode: 13,
            }),
        );
        expect(click).not.toHaveBeenCalled();
    });
});

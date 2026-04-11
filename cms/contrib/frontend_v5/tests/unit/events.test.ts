import { beforeEach, describe, expect, it, vi } from 'vitest';
import { delegate } from '../../src/modules/events';

describe('delegate', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="root">
                <ul class="list">
                    <li class="item one"><span class="label">first</span></li>
                    <li class="item two"><span class="label">second</span></li>
                </ul>
                <button class="outside">outside</button>
            </div>
            <button id="far-outside">far</button>
        `;
    });

    it('fires the handler when a click hits a matching descendant', () => {
        const root = document.getElementById('root')!;
        const handler = vi.fn();
        delegate(root, 'click', '.item', handler);

        document.querySelector<HTMLLIElement>('.item.one')!.click();
        expect(handler).toHaveBeenCalledTimes(1);
        const [event, matched] = handler.mock.calls[0]!;
        expect(event.type).toBe('click');
        expect(matched.classList.contains('one')).toBe(true);
    });

    it('matches the closest ancestor, not just direct hits', () => {
        const root = document.getElementById('root')!;
        const handler = vi.fn();
        delegate<MouseEvent, HTMLLIElement>(root, 'click', '.item', handler);

        // Click the inner span; .item should still be the matched ancestor.
        document.querySelector<HTMLSpanElement>('.item.two .label')!.click();
        expect(handler).toHaveBeenCalledTimes(1);
        expect(handler.mock.calls[0]![1].classList.contains('two')).toBe(true);
    });

    it('does not fire for clicks outside the matched selector', () => {
        const root = document.getElementById('root')!;
        const handler = vi.fn();
        delegate(root, 'click', '.item', handler);

        document.querySelector<HTMLButtonElement>('.outside')!.click();
        expect(handler).not.toHaveBeenCalled();
    });

    it('bounds matches by the root element', () => {
        // Delegate on the .list, but click a .item ancestor that's outside it.
        // (Synthetic — there's no .item outside, but there IS a button outside
        // root entirely. Verify a delegate scoped to root never sees it.)
        const root = document.getElementById('root')!;
        const handler = vi.fn();
        delegate(root, 'click', 'button', handler);

        document.getElementById('far-outside')!.click();
        expect(handler).not.toHaveBeenCalled();
    });

    it('returns an unsubscribe function that removes the listener', () => {
        const root = document.getElementById('root')!;
        const handler = vi.fn();
        const off = delegate(root, 'click', '.item', handler);

        document.querySelector<HTMLLIElement>('.item.one')!.click();
        expect(handler).toHaveBeenCalledTimes(1);

        off();
        document.querySelector<HTMLLIElement>('.item.two')!.click();
        expect(handler).toHaveBeenCalledTimes(1);
    });

    it('supports capture-phase delegation for non-bubbling events', () => {
        const root = document.getElementById('root')!;
        const handler = vi.fn();
        delegate(root, 'focus', '.item', handler, { capture: true });

        // Make .item focusable so jsdom will dispatch focus to it.
        const item = document.querySelector<HTMLLIElement>('.item.one')!;
        item.tabIndex = 0;
        item.focus();

        expect(handler).toHaveBeenCalledTimes(1);
    });

    it('supports document as the delegation root', () => {
        const handler = vi.fn();
        delegate(document, 'click', '.item', handler);

        document.querySelector<HTMLLIElement>('.item.one')!.click();
        expect(handler).toHaveBeenCalledTimes(1);
    });

    it('passes the original event object unchanged', () => {
        const root = document.getElementById('root')!;
        const received: Event[] = [];
        delegate(root, 'click', '.item', (e) => received.push(e));

        document.querySelector<HTMLLIElement>('.item.one')!.click();
        expect(received[0]).toBeInstanceOf(MouseEvent);
        expect(received[0]!.type).toBe('click');
    });
});

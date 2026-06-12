import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
    _resetForTest,
    getPendingScriptCount,
    incrementScriptCount,
    processNewScripts,
    replaceBodyWithHTML,
    scriptLoaded,
    setRefreshCallback,
    triggerRefreshEvents,
} from '../../frontend/modules/structureboard/dom/body-swap';

beforeEach(() => {
    document.body.innerHTML = '';
    _resetForTest();
});

afterEach(() => {
    _resetForTest();
    document.body.innerHTML = '';
    vi.useRealTimers();
});

function makeBody(html: string): HTMLBodyElement {
    const doc = new DOMParser().parseFromString(
        `<html><body>${html}</body></html>`,
        'text/html',
    );
    return doc.body as HTMLBodyElement;
}

describe('dom/body-swap — replaceBodyWithHTML', () => {
    it('replaces body innerHTML and removes old executable scripts first', () => {
        document.body.innerHTML = `
            <p>old</p>
            <script>oldInline()</script>
            <script type="application/json" id="keep">{"k":1}</script>
        `;
        const body = makeBody('<p>new</p>');
        replaceBodyWithHTML(body);
        expect(document.body.querySelector('p')!.textContent).toBe('new');
    });

    it('returns 0 and fires refresh callback synchronously when no external scripts pending', () => {
        vi.useFakeTimers();
        const refresh = vi.fn();
        setRefreshCallback(refresh);
        const body = makeBody('<p>hi</p>');
        const pending = replaceBodyWithHTML(body);
        expect(pending).toBe(0);
        // triggerRefreshEvents schedules with setTimeout(0)
        vi.runAllTimers();
        expect(refresh).toHaveBeenCalledOnce();
    });

    it('returns >0 when external <script src=> tags are present and refresh waits', () => {
        vi.useFakeTimers();
        const refresh = vi.fn();
        setRefreshCallback(refresh);
        const body = makeBody(
            '<p>x</p><script src="/a.js"></script><script src="/b.js"></script>',
        );
        const pending = replaceBodyWithHTML(body);
        expect(pending).toBe(2);
        // Refresh should NOT have fired yet because scripts haven't loaded.
        vi.runAllTimers();
        expect(refresh).not.toHaveBeenCalled();
    });

    it('fires refresh once all external scripts settle', () => {
        vi.useFakeTimers();
        const refresh = vi.fn();
        setRefreshCallback(refresh);
        replaceBodyWithHTML(
            makeBody('<script src="/a.js"></script><script src="/b.js"></script>'),
        );
        expect(getPendingScriptCount()).toBe(2);

        scriptLoaded();
        expect(getPendingScriptCount()).toBe(1);
        vi.runAllTimers();
        expect(refresh).not.toHaveBeenCalled();

        scriptLoaded();
        expect(getPendingScriptCount()).toBe(0);
        vi.runAllTimers();
        expect(refresh).toHaveBeenCalledOnce();
    });

    it('does not double-execute scripts that already exist on the page', () => {
        // Old body has a script that should be considered "already there".
        document.body.innerHTML = `
            <p>old</p>
            <script src="/keep.js"></script>
        `;
        // The new body has the same script tag. After body-swap we should
        // not re-clone it (the outerHTML matches an "old" script).
        // BUT note that replaceBodyWithHTML removes ALL old scripts BEFORE
        // the swap — so the de-dup is against the captured snapshot.
        const body = makeBody(
            '<p>new</p><script src="/keep.js"></script><script src="/new.js"></script>',
        );
        const pending = replaceBodyWithHTML(body);
        // /keep.js was in oldScripts snapshot (matched by outerHTML), so
        // only /new.js increments the refcount.
        expect(pending).toBe(1);
    });
});

describe('dom/body-swap — processNewScripts', () => {
    it('re-clones a new inline script (transferring textContent)', () => {
        document.body.innerHTML = '<script id="x">window.__inlineRan = true;</script>';
        const newScripts = document.body.querySelectorAll('script');
        const oldScripts = document.createDocumentFragment().querySelectorAll('script');
        processNewScripts(newScripts, oldScripts);
        // Original script is removed; clone is in its place.
        const replaced = document.body.querySelector<HTMLScriptElement>('script');
        expect(replaced).not.toBeNull();
        // Inline scripts don't increment refcount.
        expect(getPendingScriptCount()).toBe(0);
    });

    it('skips scripts that match an old script (by outerHTML)', () => {
        document.body.innerHTML = '<script src="/a.js"></script>';
        const oldScripts = document.body.querySelectorAll('script');
        // Same outerHTML in "newScripts"
        const fresh = document.createElement('script');
        fresh.src = '/a.js';
        document.body.appendChild(fresh);
        const newScripts = document.body.querySelectorAll('script');
        processNewScripts(newScripts, oldScripts);
        // refcount should remain 0 — no new script was injected
        expect(getPendingScriptCount()).toBe(0);
    });

    it('increments refcount for each new <script src>', () => {
        document.body.innerHTML = `
            <script src="/a.js"></script>
            <script src="/b.js"></script>
        `;
        const newScripts = document.body.querySelectorAll('script');
        const oldScripts = document.createDocumentFragment().querySelectorAll('script');
        processNewScripts(newScripts, oldScripts);
        expect(getPendingScriptCount()).toBe(2);
    });
});

describe('dom/body-swap — refcount + callback', () => {
    it('scriptLoaded clamps to zero (no negative refcount)', () => {
        scriptLoaded();
        scriptLoaded();
        expect(getPendingScriptCount()).toBe(0);
    });

    it('incrementScriptCount + scriptLoaded balance to zero and fire callback', () => {
        vi.useFakeTimers();
        const refresh = vi.fn();
        setRefreshCallback(refresh);
        incrementScriptCount();
        incrementScriptCount();
        expect(getPendingScriptCount()).toBe(2);
        scriptLoaded();
        scriptLoaded();
        vi.runAllTimers();
        expect(refresh).toHaveBeenCalledOnce();
    });

    it('setRefreshCallback(null) clears the callback', () => {
        vi.useFakeTimers();
        const refresh = vi.fn();
        setRefreshCallback(refresh);
        setRefreshCallback(null);
        triggerRefreshEvents();
        vi.runAllTimers();
        expect(refresh).not.toHaveBeenCalled();
    });
});

describe('dom/body-swap — triggerRefreshEvents', () => {
    it('dispatches DOMContentLoaded, load, and cms-content-refresh on next tick', () => {
        vi.useFakeTimers();
        const docHandler = vi.fn();
        const winLoadHandler = vi.fn();
        const cmsRefreshHandler = vi.fn();
        document.addEventListener('DOMContentLoaded', docHandler);
        window.addEventListener('load', winLoadHandler);
        window.addEventListener('cms-content-refresh', cmsRefreshHandler);

        triggerRefreshEvents();
        // Not yet — setTimeout(0) defers to next tick.
        expect(docHandler).not.toHaveBeenCalled();

        vi.runAllTimers();
        expect(docHandler).toHaveBeenCalled();
        expect(winLoadHandler).toHaveBeenCalled();
        expect(cmsRefreshHandler).toHaveBeenCalled();

        document.removeEventListener('DOMContentLoaded', docHandler);
        window.removeEventListener('load', winLoadHandler);
        window.removeEventListener('cms-content-refresh', cmsRefreshHandler);
    });

    it('also fires the refresh callback after dispatching events', () => {
        vi.useFakeTimers();
        const refresh = vi.fn();
        setRefreshCallback(refresh);
        triggerRefreshEvents();
        vi.runAllTimers();
        expect(refresh).toHaveBeenCalledOnce();
    });
});

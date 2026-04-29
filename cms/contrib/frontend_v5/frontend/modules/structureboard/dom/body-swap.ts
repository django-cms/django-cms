/*
 * Body-swap pipeline. Replaces the live `<body>` with new HTML and
 * re-executes scripts that weren't already on the page.
 *
 * Mirrors legacy `_replaceBodyWithHTML`, `_processNewScripts`,
 * `_scriptLoaded`, `_triggerRefreshEvents`. Owns the pending-
 * external-scripts refcount that lets the caller know when every
 * `<script src=...>` it just attached has finished loading.
 *
 * Why scripts need the refcount
 * ─────────────────────────────
 * `innerHTML = ...` assignments do NOT execute embedded `<script>`
 * tags. Legacy works around it by removing the new scripts and
 * re-inserting clones (via `insertBefore`), which DOES trigger
 * execution. External (`src=`) scripts load asynchronously, so we
 * need to count them down before declaring the swap "done".
 */

import { elementPresent } from '../parsers/markup';

/**
 * Pending external-script load refcount. Tracks `<script src=...>`
 * elements that we've just rewired into the DOM but whose `load`
 * event hasn't fired yet.
 */
let scriptReferenceCount = 0;

/**
 * Callback invoked when the refcount hits zero (every script the
 * caller injected has finished loading). Set via `setRefreshCallback`.
 */
let refreshCallback: (() => void) | null = null;

/**
 * Wire the "all pending scripts loaded" callback. Replaces the
 * legacy approach where `_replaceBodyWithHTML` called
 * `StructureBoard._triggerRefreshEvents()` directly.
 *
 * Pass `null` to clear (used in tests).
 */
export function setRefreshCallback(cb: (() => void) | null): void {
    refreshCallback = cb;
}

/**
 * Replace the live `<body>` HTML with the contents of `body`,
 * re-executing any `<script>` tags that weren't already on the page.
 *
 * `body` should be an HTMLBodyElement parsed from the server
 * response (the caller controls parsing). All non-JSON scripts on
 * the live document body are removed first, then `innerHTML` is
 * swapped, then `processNewScripts` re-clones any new scripts to
 * trigger execution.
 *
 * Mirrors legacy `_replaceBodyWithHTML`.
 *
 * Returns the count of pending external scripts. When 0, the
 * `refreshCallback` fires synchronously.
 */
export function replaceBodyWithHTML(body: HTMLElement): number {
    // Snapshot old scripts (excluding JSON blobs that aren't
    // executable) for `_processNewScripts`'s "is this already here?"
    // comparison.
    const oldScripts = document.body.querySelectorAll(
        'script:not([type="application/json"])',
    );
    oldScripts.forEach((script) => script.remove());

    document.body.innerHTML = body.innerHTML;

    const newScripts = document.body.querySelectorAll(
        'script:not([type="application/json"])',
    );
    processNewScripts(newScripts, oldScripts);

    // If no external scripts are pending, fire immediately.
    if (scriptReferenceCount === 0) {
        triggerRefreshEvents();
    }
    return scriptReferenceCount;
}

/**
 * Re-clone any `<script>` tag in `newScripts` that doesn't already
 * exist (by outerHTML) in `oldScripts`. The clone replaces the
 * original — that's what triggers browser execution.
 *
 * External scripts (`src=`) increment the pending refcount; their
 * load/error event decrements it. Inline scripts run synchronously
 * during `insertBefore` and don't participate in the refcount.
 *
 * Mirrors legacy `_processNewScripts`.
 */
export function processNewScripts(
    newScripts: NodeListOf<Element>,
    oldScripts: NodeListOf<Element>,
): void {
    newScripts.forEach((script) => {
        if (elementPresent(Array.from(oldScripts), script)) return;

        const replacement = document.createElement('script');
        for (const attr of Array.from(script.attributes)) {
            replacement.setAttribute(attr.name, attr.value);
        }

        if ((script as HTMLScriptElement).src) {
            scriptReferenceCount += 1;
            const onSettled = (): void => scriptLoaded();
            replacement.onload = onSettled;
            replacement.onerror = onSettled;
        } else {
            replacement.textContent = script.textContent;
        }
        script.parentNode?.insertBefore(replacement, script.nextSibling);
        script.remove();
    });
}

/**
 * Decrement the pending-script refcount. When it hits zero, fire the
 * caller's refresh callback.
 *
 * Mirrors legacy `_scriptLoaded`. Public so external scripts that
 * are added outside `processNewScripts` (e.g. by sekizai 3g) can
 * participate in the refcount via `incrementScriptCount`.
 */
export function scriptLoaded(): void {
    scriptReferenceCount = Math.max(0, scriptReferenceCount - 1);
    if (scriptReferenceCount === 0) triggerRefreshEvents();
}

/**
 * External hook for callers that add `<script src=...>` themselves
 * but want the refresh callback to wait for them. Pair with
 * `scriptLoaded` on the script's load/error.
 */
export function incrementScriptCount(): void {
    scriptReferenceCount += 1;
}

/**
 * Dispatch `DOMContentLoaded` + `load` + `cms-content-refresh` on
 * the next microtask. The 0-ms `setTimeout` matches legacy timing
 * and gives third-party listeners that bind during the body swap a
 * chance to register before the refresh signal fires.
 *
 * Mirrors legacy `_triggerRefreshEvents`.
 */
export function triggerRefreshEvents(): void {
    setTimeout(() => {
        document.dispatchEvent(new Event('DOMContentLoaded'));
        window.dispatchEvent(new Event('load'));
        window.dispatchEvent(new Event('cms-content-refresh'));
        refreshCallback?.();
    }, 0);
}

/**
 * Test/migration hook: reset the module-level refcount + callback
 * so tests don't leak state.
 */
export function _resetForTest(): void {
    scriptReferenceCount = 0;
    refreshCallback = null;
}

/** Read-only access to the refcount, for tests + assertions. */
export function getPendingScriptCount(): number {
    return scriptReferenceCount;
}

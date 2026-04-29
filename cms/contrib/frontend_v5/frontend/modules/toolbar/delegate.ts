/*
 * Click delegation for toolbar buttons + AJAX helper. Port of
 * `cms.toolbar.js::_delegate`, `_openSideFrame`, `_sendPostRequest`,
 * `openAjax`.
 *
 * `delegate(anchor, ctx)` reads `data-rel` (modal | message | ajax |
 * color-toggle | sideframe) and dispatches; falls back to plain
 * navigation or POST submission.
 *
 * `openAjax(opts, ctx)` performs the loader-wrapped request and
 * either runs a callback, follows a redirect, or reloads. Errors
 * surface via the Messages API.
 *
 * The dispatcher reads ported singletons via `cms-globals` accessors
 * so the toolbar still works on a contrib-only page (where some
 * APIs may be missing) and during the strangler period.
 */

import { Helpers } from '../cms-base';
import { hideLoader, showLoader } from '../loader';
import {
    getMessages,
    getModalConstructor,
    setCmsLocked,
} from '../plugins/cms-globals';

/** Loose type for `window.CMS.API.Sideframe`. */
interface SideframeApi {
    open(opts: { url: string; animate?: boolean }): void;
}
interface SideframeConstructor {
    new (opts?: { onClose?: unknown }): SideframeApi;
}
interface PluginsApi {
    _removeAddPluginPlaceholder?(): void;
}

function getSideframeApi(): SideframeApi | undefined {
    return (
        window.CMS?.API as { Sideframe?: SideframeApi } | undefined
    )?.Sideframe;
}
function getSideframeConstructor(): SideframeConstructor | undefined {
    return (window.CMS as { Sideframe?: SideframeConstructor } | undefined)
        ?.Sideframe;
}
function getPlugins(): PluginsApi | undefined {
    return (
        window.CMS as { Plugin?: PluginsApi; _Plugin?: PluginsApi } | undefined
    )?.Plugin;
}

export interface DelegateContext {
    /** Window override for tests. */
    window?: Window;
    /** Document override for tests. */
    document?: Document;
}

export interface OpenAjaxOptions {
    url: string;
    /** Stringified JSON. Empty `'{}'` if absent. */
    post?: string | undefined;
    /** HTTP method, defaults to POST. */
    method?: string | undefined;
    /** Confirmation prompt — empty string disables. */
    text?: string | undefined;
    /** Custom callback invoked with the response instead of reloading. */
    callback?: ((response: unknown) => void) | undefined;
    /**
     * Reload behaviour after success: `'FOLLOW_REDIRECT'` reads `url`
     * from the response, any other string passes through as the
     * target URL.
     */
    onSuccess?: string | undefined;
}

/**
 * Dispatch a click on a toolbar element. Reads `data-rel` and
 * delegates to the matching API. Anchors with `cms-btn-disabled` are
 * ignored — return `false` for parity with the legacy.
 */
export function delegate(
    anchor: HTMLAnchorElement,
    ctx: DelegateContext = {},
): boolean | void {
    if (anchor.classList.contains('cms-btn-disabled')) return false;
    const target = anchor.dataset.rel;

    switch (target) {
        case 'modal':
            return openModal(anchor);
        case 'message':
            return openMessage(anchor);
        case 'ajax':
            return openAjaxFromAnchor(anchor);
        case 'color-toggle':
            return Helpers.toggleColorScheme();
        case 'sideframe': {
            const enabled = isSideframeEnabled();
            if (enabled) {
                openSideFrame(anchor);
                return;
            }
            // Fall through to default — the sideframe is disabled.
            return defaultDelegate(anchor, ctx);
        }
        default:
            return defaultDelegate(anchor, ctx);
    }
}

function defaultDelegate(
    anchor: HTMLAnchorElement,
    ctx: DelegateContext,
): void {
    if (anchor.classList.contains('cms-form-post-method')) {
        sendPostRequest(anchor, ctx);
        return;
    }
    const win = ctx.window ?? Helpers._getWindow();
    win.location.href = anchor.getAttribute('href') ?? '';
}

function openModal(anchor: HTMLAnchorElement): void {
    getPlugins()?._removeAddPluginPlaceholder?.();

    const ModalCtor = getModalConstructor();
    if (!ModalCtor) {
        // Modal not loaded — fall back to plain navigation so we
        // don't silently swallow the click.
        const href = anchor.getAttribute('href');
        if (href) Helpers._getWindow().location.href = href;
        return;
    }
    const modal = new ModalCtor({
        onClose: anchor.dataset.onClose,
    }) as { open(opts: { url: string; title?: string }): void };
    const href = anchor.getAttribute('href') ?? '';
    const opts: { url: string; title?: string } = {
        url: Helpers.updateUrlWithPath(href) + '&_popup=1',
    };
    if (anchor.dataset.name !== undefined) opts.title = anchor.dataset.name;
    modal.open(opts);
}

function openMessage(anchor: HTMLAnchorElement): void {
    const messages = getMessages();
    if (!messages) return;
    messages.open({ message: anchor.dataset.text ?? '' });
}

function openAjaxFromAnchor(anchor: HTMLAnchorElement): void {
    const post = anchor.dataset.post ?? '{}';
    void openAjax({
        url: anchor.getAttribute('href') ?? '',
        post,
        method: anchor.dataset.method,
        text: anchor.dataset.text,
        onSuccess: anchor.dataset.onSuccess,
    });
}

function isSideframeEnabled(): boolean {
    const settings = (window.CMS?.settings ?? {}) as {
        sideframe_enabled?: boolean;
    };
    return (
        typeof settings.sideframe_enabled === 'undefined' ||
        Boolean(settings.sideframe_enabled)
    );
}

function openSideFrame(anchor: HTMLAnchorElement): void {
    const existing = getSideframeApi();
    let sideframe = existing;
    if (!sideframe) {
        const Ctor = getSideframeConstructor();
        if (!Ctor) return;
        sideframe = new Ctor({ onClose: anchor.dataset.onClose });
    }
    sideframe.open({
        url: anchor.getAttribute('href') ?? '',
        animate: true,
    });
}

function sendPostRequest(
    anchor: HTMLAnchorElement,
    ctx: DelegateContext,
): void {
    const doc = ctx.document ?? document;
    const win = ctx.window ?? Helpers._getWindow();
    const formToken = doc.querySelector<HTMLInputElement>(
        'form input[name="csrfmiddlewaretoken"]',
    );
    const tokenValue =
        (formToken?.value ?? '') ||
        ((window.CMS?.config as { csrf?: string } | undefined)?.csrf ?? '');
    const form = win.document.createElement('form');
    form.style.display = 'none';
    form.action = anchor.getAttribute('href') ?? '';
    form.method = 'POST';
    const input = win.document.createElement('input');
    input.type = 'hidden';
    input.name = 'csrfmiddlewaretoken';
    input.value = tokenValue;
    form.appendChild(input);
    win.document.body.appendChild(form);
    form.submit();
}

// ────────────────────────────────────────────────────────────────────
// AJAX helper
// ────────────────────────────────────────────────────────────────────

/**
 * Confirmation-gated AJAX request. On success, runs callback /
 * follows redirect / reloads. On failure, surfaces the error via
 * the Messages API. Returns false when the user cancelled the
 * confirm prompt; otherwise returns the in-flight Promise so callers
 * can await completion.
 */
export async function openAjax(
    opts: OpenAjaxOptions,
): Promise<unknown | false> {
    const { url } = opts;
    const post = opts.post ?? '{}';
    const text = opts.text ?? '';
    const method = opts.method ?? 'POST';
    const callback = opts.callback;
    const onSuccess = opts.onSuccess;

    const confirmed = text ? Helpers.secureConfirm(text) : true;
    if (!confirmed) return false;

    showLoader();

    let response: Response;
    try {
        response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken':
                    (window.CMS?.config as { csrf?: string } | undefined)
                        ?.csrf ?? '',
            },
            body: post,
        });
    } catch (err) {
        setCmsLocked(false);
        getMessages()?.open({
            message: String(err),
            error: true,
        });
        hideLoader();
        return false;
    }

    if (!response.ok) {
        setCmsLocked(false);
        const body = await safeReadText(response);
        getMessages()?.open({
            message: `${body} | ${response.status} ${response.statusText}`,
            error: true,
        });
        hideLoader();
        return false;
    }

    const payload = await safeReadJson(response);
    setCmsLocked(false);

    if (callback) {
        callback(payload);
        hideLoader();
        return payload;
    }
    if (onSuccess) {
        if (onSuccess === 'FOLLOW_REDIRECT') {
            const redirect =
                (payload as { url?: string } | null | undefined)?.url ?? null;
            Helpers.reloadBrowser(redirect);
        } else {
            Helpers.reloadBrowser(onSuccess);
        }
        return payload;
    }
    Helpers.reloadBrowser();
    return payload;
}

async function safeReadText(response: Response): Promise<string> {
    try {
        return await response.text();
    } catch {
        return '';
    }
}

async function safeReadJson(response: Response): Promise<unknown> {
    try {
        return await response.json();
    } catch {
        return null;
    }
}

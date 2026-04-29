/*
 * Iframe loader for the modal — owns the URL fetch + post-load DOM
 * surgery on the rendered admin page (extract messages, rewrite
 * target attributes, hook up form submission, mount footer buttons,
 * decide whether the modal should close immediately on save).
 *
 * Lives behind a single `loadIframe(opts)` entry point that the
 * Modal class delegates to. Returns a teardown for the iframe load
 * listener.
 *
 * Mirrors `_loadIframe` from the legacy modal — kept as a function
 * rather than a class so we can iterate without lifecycle.
 */

import { Helpers } from '../cms-base';
import { hideLoader, showLoader } from '../loader';
import { ChangeTracker } from '../changetracker';
import {
    getCmsConfig,
    getMessages,
} from '../plugins/cms-globals';
import { trap } from '../trap';
import { renderBreadcrumbs, type Breadcrumb } from './breadcrumb';
import { renderButtons } from './buttons';
import { setupCtrlEnterSave } from './ctrl-enter';

const SHOW_LOADER_TIMEOUT = 500;

export interface LoadIframeOptions {
    url: string;
    title?: string | undefined;
    name?: string | undefined;
    breadcrumbs?: Breadcrumb[] | undefined;
}

export interface IframeLoaderContext {
    modal: HTMLElement;
    frame: HTMLElement;
    modalBody: HTMLElement;
    modalButtons: HTMLElement;
    breadcrumb: HTMLElement;
    titlePrefix: HTMLElement;
    titleSuffix: HTMLElement;
    /** Reads the current `saved` flag (modified by load handler). */
    getSaved: () => boolean;
    setSaved: (value: boolean) => void;
    setHideFrame: (value: boolean) => void;
    /** Reference to the modal's onClose option — read here because
     * the cancel handler may have nulled it. */
    getOnClose: () => string | false | null | undefined;
    /** True if the modal should reload the page after a successful
     * save with messages. */
    enforceReload: boolean;
    /** True if the modal should close on success even without onClose. */
    enforceClose: boolean;
    /** Invoked when the modal should close (cancel / save / error). */
    close: () => void;
    /** Set when ChangeTracker reports dirty form on close. */
    setTracker: (tracker: ChangeTracker | null) => void;
    /** Recursive call back into the loader (re-renders the same modal). */
    loadIframe: (opts: LoadIframeOptions) => void;
}

export function loadIframe(
    ctx: IframeLoaderContext,
    opts: LoadIframeOptions,
): void {
    const url = Helpers.makeURL(opts.url);
    const title = opts.title ?? '';
    const breadcrumbs = opts.breadcrumbs;

    showLoader();

    ctx.modal.classList.remove('cms-modal-markup');
    ctx.modal.classList.add('cms-modal-iframe');

    if (renderBreadcrumbs(ctx.breadcrumb, breadcrumbs)) {
        ctx.modal.classList.add('cms-modal-has-breadcrumb');
    } else {
        ctx.modal.classList.remove('cms-modal-has-breadcrumb');
    }

    const iframe = document.createElement('iframe');
    iframe.tabIndex = 0;
    iframe.src = url;
    iframe.frameBorder = '0';
    iframe.style.visibility = 'hidden';

    ctx.titlePrefix.textContent = title;
    ctx.titleSuffix.textContent = '';

    // Hide any previous iframe.
    ctx.frame
        .querySelectorAll<HTMLElement>('iframe')
        .forEach((f) => {
            f.style.visibility = 'hidden';
        });

    const loaderTimeout = window.setTimeout(() => {
        ctx.modalBody.classList.add('cms-loader');
    }, SHOW_LOADER_TIMEOUT);

    iframe.addEventListener('load', () => {
        window.clearTimeout(loaderTimeout);
        handleIframeLoad(iframe, ctx, opts);
    });

    ctx.frame.replaceChildren(iframe);
}

function handleIframeLoad(
    iframe: HTMLIFrameElement,
    ctx: IframeLoaderContext,
    opts: LoadIframeOptions,
): void {
    let doc: Document | null = null;
    let body: HTMLElement | null = null;
    try {
        doc = iframe.contentDocument;
        body = doc?.body ?? null;
    } catch {
        // Cross-origin — surface the error and bail out.
        getMessages()?.open({
            message: `<strong>${
                (getCmsConfig() as { lang?: { errorLoadingEditForm?: string } })
                    .lang?.errorLoadingEditForm ?? ''
            }</strong>`,
            error: true,
            delay: 0,
        });
        ctx.close();
        return;
    }
    if (!doc || !body) {
        ctx.close();
        return;
    }

    trap(body);

    // Detect server-side redirect signal (`a.cms-view-new-object`).
    const redirect = body.querySelector<HTMLAnchorElement>(
        'a.cms-view-new-object',
    );
    if (redirect) {
        Helpers.reloadBrowser(redirect.href);
        return;
    }

    const closeFrameMarker = body.classList.contains('cms-close-frame');
    const popupResponse = body.querySelector<HTMLScriptElement>(
        'script#django-admin-popup-response-constants',
    );
    if (closeFrameMarker || popupResponse) {
        ctx.setSaved(true);
    }

    iframe.addEventListener('focus', () => {
        iframe.contentWindow?.focus();
    });

    setupCtrlEnterSave(document);
    if (iframe.contentWindow?.document) {
        setupCtrlEnterSave(iframe.contentWindow.document);
    }

    let saveSuccess = Boolean(
        doc.querySelectorAll('.messagelist :not(.error)').length,
    ) || Boolean(popupResponse);
    if (!saveSuccess) {
        saveSuccess =
            Boolean(doc.querySelectorAll('.dashboard #content-main').length) &&
            !doc.querySelectorAll('.messagelist .error').length;
    }

    // Surface admin messages in the toolbar's message bar.
    const messageList = doc.querySelector<HTMLElement>('.messagelist');
    const messages = messageList?.querySelectorAll<HTMLElement>('li') ?? [];
    if (messages.length > 0) {
        getMessages()?.open({
            message: messages[0]?.innerHTML ?? '',
        });
    }
    messageList?.remove();

    // Inject CMS helper classes.
    body.classList.add('cms-admin', 'cms-admin-modal');
    ctx.modalBody.classList.remove('cms-loader');
    hideLoader();

    if (messages.length > 0 && ctx.enforceReload) {
        ctx.modalBody.classList.add('cms-loader');
        showLoader();
        Helpers.reloadBrowser();
    }
    if (messages.length > 0 && ctx.enforceClose) {
        ctx.close();
        return;
    }

    doc.querySelectorAll<HTMLAnchorElement>('.viewsitelink').forEach((a) => {
        a.target = '_top';
    });

    renderButtonsForIframe(iframe, ctx, opts);

    const hasErrors =
        doc.querySelectorAll('.errornote').length > 0 ||
        doc.querySelectorAll('.errorlist').length > 0;
    if (hasErrors || (ctx.getSaved() && !saveSuccess)) {
        ctx.setSaved(false);
    }

    if (
        ctx.getSaved() &&
        saveSuccess &&
        !doc.querySelectorAll('.delete-confirmation').length
    ) {
        ctx.modalBody.classList.add('cms-loader');
        const onClose = ctx.getOnClose();
        if (onClose) {
            showLoader();
            Helpers.reloadBrowser(onClose);
        } else {
            // hello CKEditor
            Helpers.removeEventListener('modal-close.text-plugin');
            ctx.close();

            const dataBridge = body.querySelector<HTMLScriptElement>(
                'script#data-bridge',
            );
            if (dataBridge) {
                try {
                    Helpers.dataBridge = JSON.parse(
                        dataBridge.textContent ?? '{}',
                    );
                    Helpers.onPluginSave();
                } catch {
                    Helpers.reloadBrowser();
                }
            }
        }
        return;
    }

    if (ctx.modal.classList.contains('cms-modal-open')) {
        // Same `display: none` CSS rule trap as `.cms-structure` and
        // `.cms-submenu-dropdown-settings`: setting `''` would let
        // the rule win and hide the modal we just opened. Mirror
        // jQuery `.show()` and force `'block'`.
        ctx.modal.style.display = 'block';
    }
    iframe.style.display = '';

    // Title — pull from `#content h1` if not provided.
    const innerTitle = doc.querySelector<HTMLElement>('#content h1');
    if (
        opts.title === undefined &&
        ctx.titlePrefix.textContent?.trim() === ''
    ) {
        const bc = doc.querySelector<HTMLElement>('.breadcrumbs');
        if (bc) {
            const parts = bc.textContent?.split('›') ?? [];
            const last = parts[parts.length - 1]?.trim() ?? '';
            ctx.titlePrefix.textContent = last;
        }
    }
    if (ctx.titlePrefix.textContent?.trim() === '') {
        ctx.titlePrefix.textContent = innerTitle?.textContent ?? '';
    } else {
        ctx.titleSuffix.textContent = innerTitle?.textContent ?? '';
    }
    innerTitle?.remove();

    iframe.style.visibility = 'visible';
    iframe.dataset.ready = 'true';

    // Focus the iframe body if nothing else is focused there.
    setTimeout(() => {
        const innerDoc = iframe.contentDocument;
        if (!innerDoc?.documentElement) return;
        const hasFocus =
            innerDoc.activeElement &&
            innerDoc.activeElement !== innerDoc.body;
        if (!hasFocus) iframe.focus();
    }, 0);

    // Wire up ChangeTracker against the loaded iframe.
    const tracker = new ChangeTracker(iframe);
    ctx.setTracker(tracker);
}

function renderButtonsForIframe(
    iframe: HTMLIFrameElement,
    ctx: IframeLoaderContext,
    _opts: LoadIframeOptions,
): void {
    const lang = (
        getCmsConfig() as { lang?: { cancel?: string } }
    ).lang;
    renderButtons({
        iframe,
        container: ctx.modalButtons,
        cancelLabel: lang?.cancel ?? 'Cancel',
        onCancel: ctx.close,
        setHideFrame: ctx.setHideFrame,
        setSaved: ctx.setSaved,
        modal: ctx.modal,
        setBodyLoader: (v) => {
            if (v) ctx.modalBody.classList.add('cms-loader');
            else ctx.modalBody.classList.remove('cms-loader');
        },
        loadIframe: (opts) =>
            ctx.loadIframe({ url: opts.url, title: opts.name }),
    });
}

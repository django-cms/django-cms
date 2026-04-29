/*
 * Sideframe — slide-in iframe panel for the toolbar (page tree,
 * settings, etc.). Mirrors `cms.sideframe.js`. Public surface:
 *
 *   class Sideframe {
 *       constructor(options?)
 *       open({ url, animate? }): this | false
 *       close(): void
 *   }
 *
 * Implementation differs from legacy in three places:
 *   - Animation uses a CSS `width` transition instead of jQuery
 *     `animate()`. The same visible behaviour without runtime
 *     interpolation. Falls back to `setTimeout` for the post-hide
 *     `display: none` so closing is symmetric with legacy.
 *   - jQuery's `forceRerenderOnIOS` workaround is dropped — modern
 *     iOS no longer exhibits the iframe-size cache bug that
 *     workaround addressed.
 *   - The 100ms URL-polling interval is preserved verbatim — it's a
 *     load-bearing hack to track in-iframe navigation (the iframe
 *     `load` event only fires on full document loads, not the
 *     SPA-style navigations Django admin sometimes does).
 */

import { Helpers, KEYS } from './cms-base';
import { hideLoader, showLoader } from './loader';
import { getCmsConfig, getMessages } from './plugins/cms-globals';

const DEFAULT_DURATION = 300;
const URL_POLL_INTERVAL = 100;

export interface SideframeOptions {
    /** URL to navigate to on close, `false`/`null` to skip. */
    onClose?: string | false | null;
    /** Animation duration in ms. */
    sideframeDuration?: number;
}

export interface SideframeOpenOptions {
    url: string;
    animate?: boolean;
}

interface SideframeUi {
    sideframe: HTMLElement;
    body: HTMLElement;
    dimmer: HTMLElement | null;
    close: HTMLElement | null;
    frame: HTMLElement;
    shim: HTMLElement | null;
    historyBack: HTMLElement | null;
    historyForward: HTMLElement | null;
}

interface History {
    back: string[];
    forward: string[];
}

export class Sideframe {
    public readonly options: Required<Omit<SideframeOptions, 'onClose'>> & {
        onClose: SideframeOptions['onClose'];
    };
    public ui!: SideframeUi;
    public history: History = { back: [], forward: [] };
    public enforceReload = false;

    private cleanups: Array<() => void> = [];
    private escListener: ((e: KeyboardEvent) => void) | null = null;
    private pageLoadInterval: ReturnType<typeof setInterval> | null = null;

    constructor(options: SideframeOptions = {}) {
        this.options = {
            onClose: false,
            sideframeDuration: DEFAULT_DURATION,
            ...options,
        };
        this.setupUi();
    }

    open(opts: SideframeOpenOptions): this | false {
        if (!opts || !opts.url) {
            throw new Error('The arguments passed to "open" were invalid.');
        }
        const settings = window.CMS?.settings as
            | { sideframe_enabled?: boolean }
            | undefined;
        if (settings?.sideframe_enabled === false) return false;

        this.bindEvents();

        if (this.ui.dimmer) this.ui.dimmer.style.display = '';
        this.ui.frame.classList.add('cms-loader');

        showLoader();

        const url = Helpers.makeURL(opts.url);
        this.loadContent(url);
        this.show(opts.animate);

        return this;
    }

    close(): void {
        if (this.ui.dimmer) this.ui.dimmer.style.display = 'none';

        const settings = (window.CMS?.settings ?? {}) as {
            sideframe?: { url: string | null; hidden: boolean };
        };
        settings.sideframe = { url: null, hidden: true };
        try {
            Helpers.setSettings(settings);
        } catch {
            /* no localStorage — non-fatal */
        }

        this.hide({ duration: this.options.sideframeDuration / 2 });

        if (this.pageLoadInterval !== null) {
            clearInterval(this.pageLoadInterval);
            this.pageLoadInterval = null;
        }
    }

    // ────────────────────────────────────────────────────────────
    // Internal
    // ────────────────────────────────────────────────────────────

    private setupUi(): void {
        const sf = document.querySelector<HTMLElement>('.cms-sideframe');
        if (!sf) {
            throw new Error(
                'Sideframe markup not found — `.cms-sideframe` is required.',
            );
        }
        this.ui = {
            sideframe: sf,
            body: document.documentElement,
            dimmer: sf.querySelector<HTMLElement>('.cms-sideframe-dimmer'),
            close: sf.querySelector<HTMLElement>('.cms-sideframe-close'),
            frame: sf.querySelector<HTMLElement>('.cms-sideframe-frame')!,
            shim: sf.querySelector<HTMLElement>('.cms-sideframe-shim'),
            historyBack: sf.querySelector<HTMLElement>(
                '.cms-sideframe-history .cms-icon-arrow-back',
            ),
            historyForward: sf.querySelector<HTMLElement>(
                '.cms-sideframe-history .cms-icon-arrow-forward',
            ),
        };
    }

    private bindEvents(): void {
        for (const c of this.cleanups) c();
        this.cleanups = [];
        this.history = { back: [], forward: [] };

        const onClose = (): void => this.close();
        this.bind(this.ui.close, 'click', onClose);
        this.bind(this.ui.dimmer, 'click', onClose);

        const onBack = (): void => {
            if (this.ui.historyBack?.classList.contains('cms-icon-disabled'))
                return;
            this.goToHistory('back');
        };
        const onForward = (): void => {
            if (this.ui.historyForward?.classList.contains('cms-icon-disabled'))
                return;
            this.goToHistory('forward');
        };
        this.bind(this.ui.historyBack, 'click', onBack);
        this.bind(this.ui.historyForward, 'click', onForward);
    }

    private bind(
        el: HTMLElement | null,
        event: string,
        handler: EventListener,
    ): void {
        if (!el) return;
        el.addEventListener(event, handler);
        this.cleanups.push(() => el.removeEventListener(event, handler));
    }

    private loadContent(url: string): void {
        const iframe = document.createElement('iframe');
        iframe.src = url;
        iframe.frameBorder = '0';
        iframe.style.display = 'none';

        iframe.addEventListener('load', () =>
            this.handleIframeLoad(iframe),
        );

        // Persist sideframe URL into CMS settings.
        const settings = (window.CMS?.settings ?? {}) as {
            sideframe?: { url?: string | null; hidden?: boolean };
            sideframe_enabled?: boolean;
        };
        settings.sideframe = settings.sideframe ?? {};
        settings.sideframe.url = url;
        settings.sideframe.hidden = false;
        settings.sideframe_enabled = true;
        try {
            Helpers.setSettings(settings);
        } catch {
            /* no storage */
        }

        // Poll the iframe's location to track in-iframe navigation
        // (admin links often navigate without firing top-level load).
        let trackedUrl = url;
        this.pageLoadInterval = setInterval(() => {
            try {
                const current = iframe.contentWindow?.location.href;
                if (
                    current &&
                    current !== trackedUrl &&
                    current !== 'about:blank'
                ) {
                    settings.sideframe!.url = current;
                    try {
                        Helpers.setSettings(settings);
                    } catch {
                        /* no storage */
                    }
                    trackedUrl = current;
                }
            } catch {
                /* cross-origin — ignore */
            }
        }, URL_POLL_INTERVAL);

        this.ui.frame.replaceChildren(iframe);
    }

    private handleIframeLoad(iframe: HTMLIFrameElement): void {
        let doc: Document | null = null;
        try {
            doc = iframe.contentDocument;
            if (!doc) throw new Error('No contentDocument');
        } catch (error) {
            getMessages()?.open({
                message: `<strong>${String(error)}</strong>`,
                error: true,
            });
            this.close();
            return;
        }

        const body = doc.body;
        body.classList.add('cms-admin', 'cms-admin-sideframe');

        this.ui.frame.classList.remove('cms-loader');
        iframe.style.display = '';

        if ((getCmsConfig() as { debug?: boolean }).debug) {
            body.classList.add('cms-debug');
        }

        // Click inside the iframe should close any open toolbar dropdown.
        const onIframeClick = (): void => {
            document.dispatchEvent(
                new MouseEvent('click', { bubbles: true }),
            );
        };
        doc.addEventListener('click', onIframeClick);
        this.cleanups.push(() =>
            doc?.removeEventListener('click', onIframeClick),
        );

        // ESC inside iframe → close.
        const onIframeKey = (e: Event): void => {
            const ke = e as KeyboardEvent;
            if (ke.keyCode === KEYS.ESC) this.close();
        };
        body.addEventListener('keydown', onIframeKey);
        this.cleanups.push(() =>
            body.removeEventListener('keydown', onIframeKey),
        );

        // Django hack: external "view site" links should target _top
        // and close the sideframe.
        doc.querySelectorAll<HTMLAnchorElement>('.viewsitelink').forEach(
            (a) => {
                a.target = '_top';
                a.addEventListener('click', () => this.close());
            },
        );

        this.addToHistory(iframe.contentWindow?.location.href ?? '');
        hideLoader();
    }

    private show(animate: boolean | undefined): void {
        this.ui.sideframe.style.display = '';
        const targetWidth = '95%';

        if (animate) {
            this.ui.sideframe.style.transition = `width ${this.options.sideframeDuration}ms`;
            // Force layout flush so the transition runs.
            void this.ui.sideframe.offsetHeight;
            this.ui.sideframe.style.width = targetWidth;
            this.ui.sideframe.style.overflow = 'visible';
        } else {
            this.ui.sideframe.style.width = targetWidth;
        }

        // ESC handler on <html>.
        if (this.escListener) {
            this.ui.body.removeEventListener('keydown', this.escListener);
        }
        const escHandler = (e: KeyboardEvent): void => {
            if (e.keyCode === KEYS.ESC) {
                this.options.onClose = null;
                this.close();
            }
        };
        this.escListener = escHandler;
        this.ui.body.addEventListener('keydown', escHandler);

        this.ui.body.classList.add('cms-prevent-scrolling');
        Helpers.preventTouchScrolling(
            document.documentElement,
            'sideframe',
        );
    }

    private hide(opts?: { duration?: number }): void {
        const duration = opts?.duration ?? this.options.sideframeDuration;
        this.ui.sideframe.style.transition = `width ${duration}ms`;
        this.ui.sideframe.style.width = '0';

        setTimeout(() => {
            this.ui.sideframe.style.display = 'none';
            this.ui.sideframe.style.transition = '';
        }, duration);

        this.ui.frame.classList.remove('cms-loader');

        if (this.escListener) {
            this.ui.body.removeEventListener('keydown', this.escListener);
            this.escListener = null;
        }
        this.ui.body.classList.remove('cms-prevent-scrolling');
        Helpers.allowTouchScrolling(
            document.documentElement,
            'sideframe',
        );
    }

    private goToHistory(direction: 'back' | 'forward'): void {
        const iframe = this.ui.frame.querySelector<HTMLIFrameElement>(
            'iframe',
        );
        if (!iframe) return;
        if (direction === 'back') {
            const popped = this.history.back.pop();
            if (popped !== undefined) this.history.forward.push(popped);
            const target =
                this.history.back[this.history.back.length - 1] ?? '';
            iframe.src = target;
        } else {
            const popped = this.history.forward.pop();
            if (popped !== undefined) {
                this.history.back.push(popped);
                iframe.src = popped;
            }
        }
        this.updateHistoryButtons();
    }

    private addToHistory(url: string): void {
        this.history.back.push(url);
        const len = this.history.back.length;
        // De-dup adjacent same URLs (admin redirects often double-fire).
        if (
            len >= 2 &&
            this.history.back[len - 1] === this.history.back[len - 2]
        ) {
            this.history.back.pop();
        }
        this.updateHistoryButtons();
    }

    private updateHistoryButtons(): void {
        if (this.history.back.length > 1) {
            this.ui.historyBack?.classList.remove('cms-icon-disabled');
        } else {
            this.ui.historyBack?.classList.add('cms-icon-disabled');
        }
        if (this.history.forward.length >= 1) {
            this.ui.historyForward?.classList.remove('cms-icon-disabled');
        } else {
            this.ui.historyForward?.classList.add('cms-icon-disabled');
        }
    }
}

export default Sideframe;

/*
 * Toast notification — the message bar that slides down from under
 * the toolbar. Mirrors legacy `cms.messages.js`.
 *
 * Public surface (read by structureboard, toolbar, content-changed
 * hook, plugin save flow):
 *
 *   class Messages {
 *       constructor(options?)
 *       open({ message, dir?, delay?, error? })
 *       close()
 *   }
 *
 * Wired onto `window.CMS.API.Messages` by the eventual toolbar bundle
 * entry. Until that lands, the class is exposed via `CMS.Messages`
 * for tests.
 *
 * Implementation notes
 * ────────────────────
 * The legacy module animated `top`/`left`/`right` via jQuery
 * `animate()`. We use CSS transitions on those properties — the live
 * stylesheet already declares `.cms-messages { transition: top 200ms,
 * left 200ms, right 200ms; }` so setting the inline value drives the
 * same animation. `fadeOut` becomes a `setTimeout` + `display: none`.
 */

const DEFAULTS = {
    /** ms — fade-out duration on close. */
    messageDuration: 300,
    /** ms — auto-close delay when delay > 0 and message is short. */
    messageDelay: 3000,
    /**
     * Character threshold above which the message is treated as
     * "long" — auto-close is disabled and the close button is shown.
     */
    messageLength: 250,
} as const;

const TOAST_WIDTH = 320;

export interface MessagesOptions {
    messageDuration?: number;
    messageDelay?: number;
    messageLength?: number;
}

export interface OpenOptions {
    /** The toast text — string or HTML. */
    message: string;
    /** Anchor: `'left' | 'right' | 'center'` (default `'center'`). */
    dir?: 'left' | 'right' | 'center';
    /**
     * Auto-close delay in ms. 0 disables auto-close (close button
     * always shown). Defaults to `options.messageDelay`.
     */
    delay?: number;
    /** When true, applies the `.cms-messages-error` red style. */
    error?: boolean;
}

interface MessagesUi {
    container: HTMLElement | null;
    toolbar: HTMLElement | null;
    messages: HTMLElement | null;
}

export class Messages {
    private readonly options: Required<MessagesOptions>;
    private ui: MessagesUi;
    private timer: ReturnType<typeof setTimeout> | null = null;
    private closeListenerCleanup: (() => void) | null = null;

    constructor(options: MessagesOptions = {}) {
        this.options = { ...DEFAULTS, ...options };
        this.ui = setupUi();
    }

    /**
     * Slide a toast in. Throws when `message` is missing — matches
     * the legacy `'arguments passed to "open" were invalid'` guard.
     */
    open(opts: OpenOptions): void {
        if (!opts || !opts.message) {
            throw new Error('The arguments passed to "open" were invalid.');
        }

        // Refresh DOM refs in case the toolbar markup was replaced
        // since construction (e.g. by structureboard's content
        // refresh).
        this.ui = setupUi();
        const messages = this.ui.messages;
        if (!messages) return;

        const dir = opts.dir ?? 'center';
        const delay = opts.delay ?? this.options.messageDelay;
        const error = opts.error ?? false;

        const inner = messages.querySelector<HTMLElement>('.cms-messages-inner');
        if (inner) inner.innerHTML = opts.message;

        messages.classList.toggle('cms-messages-error', error);

        if (this.timer !== null) {
            clearTimeout(this.timer);
            this.timer = null;
        }

        // Toolbar height (toolbar.outerHeight(true) in jQuery — includes
        // margins). When toolbar is collapsed we anchor to top: 0.
        const collapsed =
            (window.CMS as { settings?: { toolbar?: string } } | undefined)
                ?.settings?.toolbar === 'collapsed';
        const toolbarHeight = collapsed
            ? 0
            : this.ui.toolbar
              ? outerHeightWithMargins(this.ui.toolbar)
              : 0;

        const messageHeight = outerHeightWithMargins(messages);

        // Wire up close button. Re-bind every open since `messages`
        // may have been re-rendered.
        const closeBtn = messages.querySelector<HTMLElement>(
            '.cms-messages-close',
        );
        if (closeBtn) {
            closeBtn.style.display = 'none';
            this.closeListenerCleanup?.();
            const onClose = (): void => this.close();
            closeBtn.addEventListener('click', onClose);
            this.closeListenerCleanup = (): void =>
                closeBtn.removeEventListener('click', onClose);
        }

        // Pre-position above the toolbar (off-screen for direction
        // animations), then show.
        messages.style.top = `${-messageHeight}px`;
        messages.style.display = '';

        // Direction-specific positioning.
        switch (dir) {
            case 'left':
                Object.assign(messages.style, {
                    top: `${toolbarHeight}px`,
                    left: `${-TOAST_WIDTH}px`,
                    right: 'auto',
                    marginLeft: '0',
                });
                // Force a layout flush so the transition runs.
                void messages.offsetHeight;
                messages.style.left = '0';
                break;
            case 'right':
                Object.assign(messages.style, {
                    top: `${toolbarHeight}px`,
                    right: `${-TOAST_WIDTH}px`,
                    left: 'auto',
                    marginLeft: '0',
                });
                void messages.offsetHeight;
                messages.style.right = '0';
                break;
            default:
                Object.assign(messages.style, {
                    left: '50%',
                    right: 'auto',
                    marginLeft: `${-TOAST_WIDTH / 2}px`,
                });
                void messages.offsetHeight;
                messages.style.top = `${toolbarHeight}px`;
        }

        // Auto-close, unless suppressed by delay <= 0 or long message.
        const shouldAutoClose =
            delay > 0 && opts.message.length <= this.options.messageLength;
        if (!shouldAutoClose) {
            if (closeBtn) closeBtn.style.display = '';
        } else {
            this.timer = setTimeout(() => this.close(), delay);
        }
    }

    /** Fade the toast out. Idempotent. */
    close(): void {
        const messages = this.ui.messages;
        if (!messages) return;
        const duration = this.options.messageDuration;
        messages.style.transition = `opacity ${duration}ms`;
        messages.style.opacity = '0';
        setTimeout(() => {
            messages.style.display = 'none';
            messages.style.opacity = '';
            messages.style.transition = '';
        }, duration);
        if (this.timer !== null) {
            clearTimeout(this.timer);
            this.timer = null;
        }
        this.closeListenerCleanup?.();
        this.closeListenerCleanup = null;
    }
}

function setupUi(): MessagesUi {
    const container = document.querySelector<HTMLElement>('.cms');
    return {
        container,
        toolbar: container?.querySelector<HTMLElement>('.cms-toolbar') ?? null,
        messages: container?.querySelector<HTMLElement>('.cms-messages') ?? null,
    };
}

/**
 * Approximate jQuery's `.outerHeight(true)` — element height plus
 * vertical margins. Used for toolbar offset calculation.
 */
function outerHeightWithMargins(el: HTMLElement): number {
    const rect = el.getBoundingClientRect();
    const cs = window.getComputedStyle(el);
    const mt = parseFloat(cs.marginTop) || 0;
    const mb = parseFloat(cs.marginBottom) || 0;
    return rect.height + mt + mb;
}

export default Messages;

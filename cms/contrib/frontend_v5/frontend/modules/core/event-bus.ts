/*
 * cmsEvents — typed CustomEvent bus with a bidirectional jQuery bridge.
 *
 * Why this exists
 * ───────────────
 * Legacy bundles publish and subscribe to events through jQuery's
 * pub/sub: `$(CMS._eventRoot).trigger('cms-content-refresh', [data])`
 * and `$(CMS._eventRoot).on('cms-...', handler)`. Tracker #34 calls
 * for migrating off the jQuery bus to native CustomEvents — but we
 * can't flip the switch in one go, because legacy bundles are still
 * shipping jQuery-bus listeners until every bundle ports.
 *
 * The strangler contract:
 *   - New TS code uses `cmsEvents.on()` / `cmsEvents.emit()`.
 *   - During the migration window, both sides see every event:
 *       * `cmsEvents.emit(type, detail)` → native dispatch + jQuery
 *         `.trigger(type, detail)` mirror so legacy listeners fire.
 *       * `$(CMS._eventRoot).trigger(type, detail)` → mirrored back
 *         to native dispatch when at least one TS subscriber exists
 *         for `type`.
 *   - Loop prevention: a single re-entrancy flag guards both
 *     directions of the mirror.
 *   - When all consumers are TS (Phase 6 of the migration plan), call
 *     `_disableJqueryBridge()` and delete the bridge code.
 *
 * Event target identity
 * ─────────────────────
 * Native dispatch goes to a single `EventTarget` stashed on `window`
 * under a non-enumerable symbol. Vitest may reload modules in watch
 * mode, but the target is recreated on first access, so listeners
 * registered after a hot reload still find each other.
 */

const TARGET_KEY = '__cmsEventTarget__';
const BRIDGED_KEY = '__cmsEventBridgedTypes__';

interface BusWindow {
    [TARGET_KEY]?: EventTarget;
    [BRIDGED_KEY]?: Set<string>;
}

function getTarget(): EventTarget {
    const w = window as unknown as BusWindow;
    if (!w[TARGET_KEY]) w[TARGET_KEY] = new EventTarget();
    return w[TARGET_KEY];
}

function bridgedTypes(): Set<string> {
    const w = window as unknown as BusWindow;
    if (!w[BRIDGED_KEY]) w[BRIDGED_KEY] = new Set();
    return w[BRIDGED_KEY];
}

/**
 * True while this module is mirroring a dispatch in either direction.
 * Re-entrant emits / triggers fired by listeners during this window
 * are NOT mirrored, which prevents native↔jQuery loops.
 */
let bridgeInFlight = false;

export type CmsEventListener<T> = (detail: T) => void;

/** Disposable handle returned by `cmsEvents.on`. */
export type Unsubscribe = () => void;

export const cmsEvents = {
    /**
     * Subscribe to events of `type`. The returned function unsubscribes
     * (idempotent — safe to call multiple times).
     *
     * If a jQuery bus is available, also installs a one-time bridge
     * listener for this type so legacy `.trigger(type, ...)` calls
     * cross into the native dispatcher.
     */
    on<T = unknown>(type: string, listener: CmsEventListener<T>): Unsubscribe {
        const handler = (ev: Event) => {
            const detail = (ev as CustomEvent<T>).detail;
            listener(detail);
        };
        getTarget().addEventListener(type, handler);
        ensureJqueryBridge(type);
        let disposed = false;
        return () => {
            if (disposed) return;
            disposed = true;
            getTarget().removeEventListener(type, handler);
        };
    },

    /**
     * Fire `type` with `detail`. Native subscribers run first
     * (synchronously), then the jQuery mirror fires for legacy
     * subscribers. Loops are prevented by the in-flight flag.
     */
    emit<T = unknown>(type: string, detail?: T): void {
        if (bridgeInFlight) {
            // Re-entrant emit during a bridge mirror — dispatch
            // natively only, don't bounce back to jQuery.
            getTarget().dispatchEvent(new CustomEvent<T | undefined>(type, { detail }));
            return;
        }
        bridgeInFlight = true;
        try {
            getTarget().dispatchEvent(new CustomEvent<T | undefined>(type, { detail }));
            mirrorEmitToJquery(type, detail);
        } finally {
            bridgeInFlight = false;
        }
    },
};

/**
 * Minimal jQuery surface this module relies on. The full @types/jquery
 * definitions over-constrain trigger/on argument types; we only need
 * the runtime behaviour. Cast at the boundary, keep the rest typed.
 */
interface JqWrapper {
    on(type: string, handler: (event: unknown, detail?: unknown) => void): void;
    trigger(type: string, args: unknown[]): void;
}
type JqFactory = (target: unknown) => JqWrapper;

function getJqFactory(): JqFactory | undefined {
    return window.jQuery as unknown as JqFactory | undefined;
}

/**
 * Install the legacy → native bridge for `type` if jQuery and the
 * `CMS._eventRoot` are present. Idempotent per type.
 */
function ensureJqueryBridge(type: string): void {
    if (bridgedTypes().has(type)) return;
    const $ = getJqFactory();
    const root = window.CMS?._eventRoot;
    if (!$ || !root) return;
    bridgedTypes().add(type);
    try {
        // jQuery `.trigger(type, [a, b, ...])` invokes handlers as
        // `(event, a, b, ...)`. Legacy callers always pass a single
        // detail object, so `args[0]` is the detail value.
        $(root).on(type, (_ev: unknown, detail: unknown) => {
            if (bridgeInFlight) return;
            bridgeInFlight = true;
            try {
                getTarget().dispatchEvent(new CustomEvent(type, { detail }));
            } finally {
                bridgeInFlight = false;
            }
        });
    } catch {
        /* best-effort: if jQuery rejects the binding, drop silently */
    }
}

/**
 * Forward a native emit to the jQuery bus so legacy subscribers see it.
 * No-op when jQuery or the event root isn't on the page.
 */
function mirrorEmitToJquery<T>(type: string, detail: T | undefined): void {
    const $ = getJqFactory();
    const root = window.CMS?._eventRoot;
    if (!$ || !root) return;
    try {
        const args = detail === undefined ? [] : [detail];
        $(root).trigger(type, args);
    } catch {
        /* best-effort mirror */
    }
}

/**
 * Test/migration hook: drop every bridged-type registration and clear
 * the in-flight flag. After Phase 6 of the migration this whole
 * file's bridge half is deletable.
 */
export function _resetEventBusForTest(): void {
    const w = window as unknown as BusWindow;
    if (w[TARGET_KEY]) {
        // Replace the target so any leftover listeners drop off.
        w[TARGET_KEY] = new EventTarget();
    }
    bridgedTypes().clear();
    bridgeInFlight = false;
}

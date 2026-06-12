/*
 * Opposite-mode preload.
 *
 * Mirrors legacy `StructureBoard._preloadOppositeMode`. After page
 * load + a 2-second idle delay, kicks off a background fetch of the
 * mode the user is NOT currently in. The fetch goes through
 * `network/fetch.ts::requestMode` which memoises per mode, so when
 * the user toggles modes the markup is already in cache.
 *
 * Skipped when `CMS.config.settings.legacy_mode` is on (legacy_mode
 * pages don't use the structure/edit URL pair).
 */

import { requestMode } from '../network/fetch';
import { getCmsConfig } from '../../plugins/cms-globals';

const WAIT_BEFORE_PRELOADING_MS = 2000;

export interface PreloadOptions {
    /** Read-only — has structure-mode markup been loaded already? */
    isLoadedStructure(): boolean;
    /**
     * Window/host — defaults to `window`. Tests pass a stub so the
     * `load` event can be triggered synchronously.
     */
    win?: Window;
    /** Override the 2-second delay (tests use 0). */
    delayMs?: number;
}

export interface PreloadHandle {
    destroy(): void;
}

/**
 * Wire the preload trigger. The returned handle's `destroy()` releases
 * the load listener + cancels a pending preload.
 *
 * Idempotent in the legacy semantics — multiple calls bind multiple
 * listeners; legacy class always called it once. We still rely on
 * `requestMode`'s per-mode memo so duplicate triggers are cheap.
 */
export function setupOppositeModePreload(
    options: PreloadOptions,
): PreloadHandle {
    if (getCmsConfig().settings?.legacy_mode) {
        // Legacy mode: noop handle.
        return { destroy: (): void => undefined };
    }

    const win = options.win ?? window;
    const delay = options.delayMs ?? WAIT_BEFORE_PRELOADING_MS;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | null = null;

    const onLoad = (): void => {
        timer = setTimeout(() => {
            timer = null;
            const target = options.isLoadedStructure() ? 'content' : 'structure';
            // Fire-and-forget — preload errors don't surface to the user.
            void requestMode(target).catch(() => undefined);
        }, delay);
    };

    win.addEventListener('load', onLoad, {
        once: true,
        signal: controller.signal,
    });

    return {
        destroy(): void {
            controller.abort();
            if (timer !== null) {
                clearTimeout(timer);
                timer = null;
            }
        },
    };
}

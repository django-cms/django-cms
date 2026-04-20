import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { currentVersionMatches, Helpers, KEYS, uid } from '../../frontend/modules/cms-base';

describe('uid', () => {
    it('returns incrementing numbers', () => {
        const a = uid();
        const b = uid();
        const c = uid();
        expect(b).toBe(a + 1);
        expect(c).toBe(b + 1);
    });
});

describe('currentVersionMatches', () => {
    it('returns true when the version matches __CMS_VERSION__', () => {
        expect(currentVersionMatches({ version: 'test-version' })).toBe(true);
    });

    it('returns false for a different version', () => {
        expect(currentVersionMatches({ version: '0.0.0-fake' })).toBe(false);
    });

    it('returns false for undefined version', () => {
        expect(currentVersionMatches({})).toBe(false);
    });
});

describe('KEYS', () => {
    it('has expected key codes', () => {
        expect(KEYS.ENTER).toBe(13);
        expect(KEYS.ESC).toBe(27);
        expect(KEYS.TAB).toBe(9);
        expect(KEYS.SPACE).toBe(32);
        expect(KEYS.UP).toBe(38);
        expect(KEYS.DOWN).toBe(40);
    });
});

describe('Helpers.makeURL', () => {
    it('appends params to a relative URL', () => {
        const result = Helpers.makeURL('/foo/', [['bar', 'baz']]);
        expect(result).toBe('/foo/?bar=baz');
    });

    it('replaces existing params with new values', () => {
        const result = Helpers.makeURL('/foo/?bar=old', [['bar', 'new']]);
        expect(result).toBe('/foo/?bar=new');
    });

    it('adds multiple params', () => {
        const result = Helpers.makeURL('/foo/', [
            ['a', '1'],
            ['b', '2'],
        ]);
        expect(result).toContain('a=1');
        expect(result).toContain('b=2');
    });

    it('preserves absolute URLs when input is absolute', () => {
        const result = Helpers.makeURL('http://example.com/page/', [['q', 'test']]);
        expect(result.startsWith('http://example.com/page/')).toBe(true);
        expect(result).toContain('q=test');
    });

    it('decodes &amp; entities before processing', () => {
        const result = Helpers.makeURL('/foo/?a=1&amp;b=2', [['c', '3']]);
        expect(result).toContain('a=1');
        expect(result).toContain('b=2');
        expect(result).toContain('c=3');
    });

    it('preserves no leading slash when input has none', () => {
        const result = Helpers.makeURL('foo/bar/', [['x', '1']]);
        expect(result.startsWith('/')).toBe(false);
        expect(result.startsWith('foo/bar/')).toBe(true);
    });

    it('returns the URL unchanged (minus decoding) when no params are given', () => {
        expect(Helpers.makeURL('/hello/')).toBe('/hello/');
    });
});

describe('Helpers.secureConfirm', () => {
    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it('returns the confirm result when dialog was shown (long enough)', () => {
        vi.stubGlobal(
            'confirm',
            vi.fn(() => {
                // Simulate ~50ms dialog time (well above the 10ms threshold).
                const end = Date.now() + 50;
                while (Date.now() < end) {
                    // busy-wait to simulate real user delay
                }
                return false;
            }),
        );
        expect(Helpers.secureConfirm('Are you sure?')).toBe(false);
    });

    it('returns true when confirm was instant (user suppressed dialogs)', () => {
        vi.stubGlobal('confirm', vi.fn(() => false));
        // Instant return → below 10ms → secureConfirm returns true.
        expect(Helpers.secureConfirm('Are you sure?')).toBe(true);
    });
});

describe('Helpers._isStorageSupported', () => {
    it('is a boolean', () => {
        expect(typeof Helpers._isStorageSupported).toBe('boolean');
    });

    it('is true in jsdom (which has localStorage)', () => {
        expect(Helpers._isStorageSupported).toBe(true);
    });
});

describe('Helpers.setSettings / getSettings', () => {
    beforeEach(() => {
        localStorage.clear();
        window.CMS = {
            config: {
                settings: { version: 'test-version', mode: 'edit' },
            },
        };
    });

    afterEach(() => {
        localStorage.clear();
        delete (window as { CMS?: unknown }).CMS;
        vi.unstubAllGlobals();
    });

    it('setSettings writes to localStorage and returns merged settings', () => {
        const result = Helpers.setSettings({ custom: 'value' });
        expect(result.custom).toBe('value');
        expect(result.mode).toBe('edit');

        const raw = localStorage.getItem('cms_cookie');
        expect(raw).toBeTruthy();
        const parsed = JSON.parse(raw!);
        expect(parsed.custom).toBe('value');
    });

    it('getSettings reads from localStorage', () => {
        Helpers.setSettings({ foo: 'bar' });
        const result = Helpers.getSettings();
        expect(result.foo).toBe('bar');
    });

    it('getSettings re-seeds from config when version mismatches', () => {
        localStorage.setItem('cms_cookie', JSON.stringify({ version: '0.0.0', stale: true }));
        const result = Helpers.getSettings();
        expect(result.stale).toBeUndefined();
        expect(result.version).toBe('test-version');
    });

    it('getSettings re-seeds from config when localStorage is empty', () => {
        const result = Helpers.getSettings();
        expect(result.version).toBe('test-version');
        expect(result.mode).toBe('edit');
    });
});

describe('Helpers.getColorScheme / setColorScheme / toggleColorScheme', () => {
    beforeEach(() => {
        localStorage.removeItem('theme');
        document.documentElement.removeAttribute('data-theme');
        window.CMS = { config: { color_scheme: 'auto' } };
    });

    afterEach(() => {
        localStorage.removeItem('theme');
        document.documentElement.removeAttribute('data-theme');
        delete (window as { CMS?: unknown }).CMS;
    });

    it('getColorScheme reads data-theme from <html>', () => {
        document.documentElement.setAttribute('data-theme', 'dark');
        expect(Helpers.getColorScheme()).toBe('dark');
    });

    it('getColorScheme falls back to localStorage', () => {
        localStorage.setItem('theme', 'light');
        expect(Helpers.getColorScheme()).toBe('light');
    });

    it('getColorScheme falls back to CMS.config.color_scheme', () => {
        expect(Helpers.getColorScheme()).toBe('auto');
    });

    it('setColorScheme sets data-theme on <html>', () => {
        Helpers.setColorScheme('dark');
        expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    it('setColorScheme normalises invalid values to "auto"', () => {
        Helpers.setColorScheme('invalid');
        expect(document.documentElement.getAttribute('data-theme')).toBe('auto');
    });

    it('setColorScheme writes to localStorage', () => {
        Helpers.setColorScheme('light');
        expect(localStorage.getItem('theme')).toBe('light');
    });
});

describe('Helpers lodash re-exports', () => {
    it('exposes once, debounce, throttle as functions', () => {
        expect(typeof Helpers.once).toBe('function');
        expect(typeof Helpers.debounce).toBe('function');
        expect(typeof Helpers.throttle).toBe('function');
    });
});

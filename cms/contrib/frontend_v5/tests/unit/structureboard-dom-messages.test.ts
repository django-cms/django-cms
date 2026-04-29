import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { contentChanged } from '../../frontend/modules/structureboard/dom/messages';

interface CmsTestable {
    config?: Record<string, unknown>;
    settings?: Record<string, unknown>;
    _instances?: unknown[];
    _plugins?: unknown[];
    API?: { Messages?: { open?: ReturnType<typeof vi.fn>; close?: ReturnType<typeof vi.fn> } };
}

function setupCms(messages?: { open?: ReturnType<typeof vi.fn>; close?: ReturnType<typeof vi.fn> }): void {
    (window as unknown as { CMS: CmsTestable }).CMS = {
        config: {},
        settings: {},
        _instances: [],
        _plugins: [],
        ...(messages ? { API: { Messages: messages } } : {}),
    };
}

beforeEach(() => {
    document.body.innerHTML = '';
    setupCms();
});

afterEach(() => {
    document.body.innerHTML = '';
    delete (window as { CMS?: unknown }).CMS;
});

describe('dom/messages — contentChanged', () => {
    it('does NOT touch the messages API when no messages are passed', () => {
        const open = vi.fn();
        const close = vi.fn();
        setupCms({ open, close });
        contentChanged();
        expect(open).not.toHaveBeenCalled();
        expect(close).not.toHaveBeenCalled();
    });

    it('calls Messages.close() when an empty messages array is passed', () => {
        const open = vi.fn();
        const close = vi.fn();
        setupCms({ open, close });
        contentChanged([]);
        expect(close).toHaveBeenCalledOnce();
        expect(open).not.toHaveBeenCalled();
    });

    it('combines messages into a single <p>-wrapped toast', () => {
        const open = vi.fn();
        const close = vi.fn();
        setupCms({ open, close });
        contentChanged([
            { message: 'first' },
            { message: 'second' },
        ]);
        expect(close).toHaveBeenCalledOnce();
        expect(open).toHaveBeenCalledOnce();
        const arg = open.mock.calls[0]![0];
        expect(arg.message).toBe('<p>first</p><p>second</p>');
        expect(arg.error).toBe(false);
    });

    it('marks the combined toast as error when any message has error: true', () => {
        const open = vi.fn();
        setupCms({ open, close: vi.fn() });
        contentChanged([
            { message: 'ok' },
            { message: 'bad', error: true },
        ]);
        expect(open.mock.calls[0]![0].error).toBe(true);
    });

    it('marks as error when any message has level === "error"', () => {
        const open = vi.fn();
        setupCms({ open, close: vi.fn() });
        contentChanged([{ message: 'fail', level: 'error' }]);
        expect(open.mock.calls[0]![0].error).toBe(true);
    });

    it('is safe when CMS.API.Messages is missing', () => {
        setupCms();
        expect(() => contentChanged([{ message: 'x' }])).not.toThrow();
    });
});

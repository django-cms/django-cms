import { beforeEach, describe, expect, it } from 'vitest';
import {
    handleKey,
    TYPEAHEAD_RESET_MS,
    type KeyContext,
    type TypeAheadBuffer,
} from '../../frontend/modules/tree/keyboard-nav';
import { TreeState } from '../../frontend/modules/tree/state';

/**
 * Build a fixture tree with readable labels:
 *
 *   Alpha
 *   ├─ Apple
 *   │  ├─ Apricot
 *   │  └─ Avocado
 *   └─ Banana
 *   Cherry
 *   └─ Citrus
 */
interface Fruit {
    label: string;
}

const buildFixture = () =>
    TreeState.from<Fruit>([
        { id: 'alpha', parentId: null, data: { label: 'Alpha' } },
        { id: 'apple', parentId: 'alpha', data: { label: 'Apple' } },
        { id: 'apricot', parentId: 'apple', data: { label: 'Apricot' } },
        { id: 'avocado', parentId: 'apple', data: { label: 'Avocado' } },
        { id: 'banana', parentId: 'alpha', data: { label: 'Banana' } },
        { id: 'cherry', parentId: null, data: { label: 'Cherry' } },
        { id: 'citrus', parentId: 'cherry', data: { label: 'Citrus' } },
    ]);

/** Build a KeyContext with defaults suitable for most tests. */
const mkCtx = (overrides: Partial<KeyContext> = {}): KeyContext => {
    const tree = buildFixture();
    return {
        tree,
        expandedIds: new Set(),
        focusedId: null,
        getLabel: (id) => tree.get(id)?.data.label ?? '',
        typeAhead: { text: '', lastKeyTime: 0 },
        now: 1000,
        ...overrides,
    };
};

describe('handleKey — empty tree', () => {
    it('returns noop for any key on an empty tree', () => {
        const tree = TreeState.from<Fruit>([]);
        const ctx: KeyContext = {
            tree,
            expandedIds: new Set(),
            focusedId: null,
            getLabel: () => '',
            typeAhead: { text: '', lastKeyTime: 0 },
            now: 1000,
        };
        for (const key of ['ArrowDown', 'ArrowUp', 'Home', 'End', 'Enter', 'a']) {
            expect(handleKey(ctx, key).command).toEqual({ kind: 'noop' });
        }
    });
});

describe('handleKey — ArrowDown', () => {
    it('focuses the first visible item when no focus is set', () => {
        const { command } = handleKey(mkCtx(), 'ArrowDown');
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('moves focus to the next visible item (collapsed state)', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'ArrowDown');
        // Alpha is collapsed, so its children are hidden. Next visible = cherry.
        expect(command).toEqual({ kind: 'focus', id: 'cherry' });
    });

    it('descends into expanded children', () => {
        const { command } = handleKey(
            mkCtx({ focusedId: 'alpha', expandedIds: new Set(['alpha']) }),
            'ArrowDown',
        );
        expect(command).toEqual({ kind: 'focus', id: 'apple' });
    });

    it('does not skip past deep expansion', () => {
        const { command } = handleKey(
            mkCtx({
                focusedId: 'apple',
                expandedIds: new Set(['alpha', 'apple']),
            }),
            'ArrowDown',
        );
        expect(command).toEqual({ kind: 'focus', id: 'apricot' });
    });

    it('is a noop on the last visible item', () => {
        // Everything collapsed → last visible = cherry.
        const { command } = handleKey(mkCtx({ focusedId: 'cherry' }), 'ArrowDown');
        expect(command).toEqual({ kind: 'noop' });
    });

    it('focuses first visible if focusedId is unknown', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'ghost' }), 'ArrowDown');
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });
});

describe('handleKey — ArrowUp', () => {
    it('focuses the first visible item when no focus is set', () => {
        const { command } = handleKey(mkCtx(), 'ArrowUp');
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('moves focus to the previous visible item', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'cherry' }), 'ArrowUp');
        // All collapsed → previous visible before cherry = alpha.
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('is a noop on the first visible item', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'ArrowUp');
        expect(command).toEqual({ kind: 'noop' });
    });

    it('ascends out of expanded children', () => {
        const { command } = handleKey(
            mkCtx({ focusedId: 'apple', expandedIds: new Set(['alpha']) }),
            'ArrowUp',
        );
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });
});

describe('handleKey — ArrowRight', () => {
    it('expands a closed parent, leaves focus where it is', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'ArrowRight');
        expect(command).toEqual({ kind: 'expand', id: 'alpha' });
    });

    it('focuses first child on an already-open parent', () => {
        const { command } = handleKey(
            mkCtx({ focusedId: 'alpha', expandedIds: new Set(['alpha']) }),
            'ArrowRight',
        );
        expect(command).toEqual({ kind: 'focus', id: 'apple' });
    });

    it('is a noop on a leaf node', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'banana' }), 'ArrowRight');
        expect(command).toEqual({ kind: 'noop' });
    });

    it('is a noop when there is no focus', () => {
        const { command } = handleKey(mkCtx(), 'ArrowRight');
        expect(command).toEqual({ kind: 'noop' });
    });
});

describe('handleKey — ArrowLeft', () => {
    it('collapses an open parent, leaves focus where it is', () => {
        const { command } = handleKey(
            mkCtx({ focusedId: 'alpha', expandedIds: new Set(['alpha']) }),
            'ArrowLeft',
        );
        expect(command).toEqual({ kind: 'collapse', id: 'alpha' });
    });

    it('focuses parent on a closed parent', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'apple' }), 'ArrowLeft');
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('focuses parent on a leaf node with a parent', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'banana' }), 'ArrowLeft');
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('is a noop on a root leaf', () => {
        // Cherry IS a parent in the fixture, so use citrus's root scenario.
        // Actually: let's test citrus itself collapsed — it IS a leaf, but
        // has a parent. So: create a tree where we test a root leaf.
        const tree = TreeState.from<Fruit>([
            { id: 'solo', parentId: null, data: { label: 'Solo' } },
        ]);
        const { command } = handleKey(
            {
                tree,
                expandedIds: new Set(),
                focusedId: 'solo',
                getLabel: () => 'Solo',
                typeAhead: { text: '', lastKeyTime: 0 },
                now: 0,
            },
            'ArrowLeft',
        );
        expect(command).toEqual({ kind: 'noop' });
    });

    it('is a noop on a root parent that is closed', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'ArrowLeft');
        expect(command).toEqual({ kind: 'noop' });
    });
});

describe('handleKey — Home / End', () => {
    it('Home focuses the first visible item', () => {
        const { command } = handleKey(
            mkCtx({ focusedId: 'cherry', expandedIds: new Set(['alpha']) }),
            'Home',
        );
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('End focuses the last visible item (collapsed)', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'End');
        expect(command).toEqual({ kind: 'focus', id: 'cherry' });
    });

    it('End focuses the deepest last visible item when expanded', () => {
        const { command } = handleKey(
            mkCtx({
                focusedId: 'alpha',
                expandedIds: new Set(['alpha', 'apple', 'cherry']),
            }),
            'End',
        );
        expect(command).toEqual({ kind: 'focus', id: 'citrus' });
    });
});

describe('handleKey — Enter / Space', () => {
    it('Enter on a closed parent expands it', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'Enter');
        expect(command).toEqual({ kind: 'expand', id: 'alpha' });
    });

    it('Enter on an open parent collapses it', () => {
        const { command } = handleKey(
            mkCtx({ focusedId: 'alpha', expandedIds: new Set(['alpha']) }),
            'Enter',
        );
        expect(command).toEqual({ kind: 'collapse', id: 'alpha' });
    });

    it('Enter on a leaf activates it', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'banana' }), 'Enter');
        expect(command).toEqual({ kind: 'activate', id: 'banana' });
    });

    it('Space behaves the same as Enter (parent → toggle)', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), ' ');
        expect(command).toEqual({ kind: 'expand', id: 'alpha' });
    });

    it('Space on a leaf activates it', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'banana' }), ' ');
        expect(command).toEqual({ kind: 'activate', id: 'banana' });
    });

    it('Spacebar (legacy IE name) also works', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'banana' }), 'Spacebar');
        expect(command).toEqual({ kind: 'activate', id: 'banana' });
    });

    it('is a noop when no focus', () => {
        const { command } = handleKey(mkCtx(), 'Enter');
        expect(command).toEqual({ kind: 'noop' });
    });
});

describe('handleKey — type-ahead', () => {
    it('single char focuses the next matching visible item', () => {
        const { command, typeAhead } = handleKey(mkCtx({ focusedId: 'alpha' }), 'c');
        // From alpha, next match for "c" is cherry.
        expect(command).toEqual({ kind: 'focus', id: 'cherry' });
        expect(typeAhead.text).toBe('c');
        expect(typeAhead.lastKeyTime).toBe(1000);
    });

    it('is case-insensitive', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), 'C');
        expect(command).toEqual({ kind: 'focus', id: 'cherry' });
    });

    it('wraps around to the beginning if no later match', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'cherry' }), 'a');
        expect(command).toEqual({ kind: 'focus', id: 'alpha' });
    });

    it('cycles through matches with repeated same-char presses', () => {
        // Expand alpha + apple so apricot and avocado are visible.
        const ctx = mkCtx({
            focusedId: 'alpha',
            expandedIds: new Set(['alpha', 'apple']),
        });
        // First "a" from alpha → apple (next visible starting with "a").
        const r1 = handleKey(ctx, 'a');
        expect(r1.command).toEqual({ kind: 'focus', id: 'apple' });

        // Simulate caller applying focus move, same buffer state.
        // Second "a" would concatenate to "aa", which matches nothing —
        // UNLESS the buffer timed out. Test the repeat-cycle behavior
        // by waiting past the reset window.
        const ctx2 = mkCtx({
            focusedId: 'apple',
            expandedIds: new Set(['alpha', 'apple']),
            typeAhead: r1.typeAhead,
            now: r1.typeAhead.lastKeyTime + TYPEAHEAD_RESET_MS + 1,
        });
        const r2 = handleKey(ctx2, 'a');
        // Buffer reset → single "a" again → next "a" from apple = apricot.
        expect(r2.command).toEqual({ kind: 'focus', id: 'apricot' });
        expect(r2.typeAhead.text).toBe('a');
    });

    it('multi-char search within reset window (from focused item)', () => {
        const ctx = mkCtx({
            focusedId: 'alpha',
            expandedIds: new Set(['alpha', 'apple']),
        });
        // Type "ap"
        const r1 = handleKey(ctx, 'a');
        // r1 focuses apple (first "a" after alpha).
        const r2 = handleKey(
            {
                ...ctx,
                focusedId: 'apple',
                typeAhead: r1.typeAhead,
                now: r1.typeAhead.lastKeyTime + 50,
            },
            'p',
        );
        expect(r2.typeAhead.text).toBe('ap');
        // Multi-char starts from focused item (apple), matches apple.
        expect(r2.command).toEqual({ kind: 'focus', id: 'apple' });
    });

    it('multi-char where the new string matches a deeper node', () => {
        const ctx = mkCtx({
            focusedId: 'alpha',
            expandedIds: new Set(['alpha', 'apple']),
            typeAhead: { text: 'apr', lastKeyTime: 999 },
            now: 1000,
        });
        // Buffer already has "apr", typing "i" → "apri" matches apricot.
        const { command, typeAhead } = handleKey(ctx, 'i');
        expect(typeAhead.text).toBe('apri');
        expect(command).toEqual({ kind: 'focus', id: 'apricot' });
    });

    it('buffer resets after TYPEAHEAD_RESET_MS of inactivity', () => {
        const ctx = mkCtx({
            focusedId: 'alpha',
            typeAhead: { text: 'xyz', lastKeyTime: 0 },
            now: TYPEAHEAD_RESET_MS + 100,
        });
        const { typeAhead } = handleKey(ctx, 'c');
        // New buffer should be just "c", not "xyzc".
        expect(typeAhead.text).toBe('c');
    });

    it('no match → noop, but still updates the buffer', () => {
        const { command, typeAhead } = handleKey(mkCtx({ focusedId: 'alpha' }), 'z');
        expect(command).toEqual({ kind: 'noop' });
        expect(typeAhead.text).toBe('z');
        expect(typeAhead.lastKeyTime).toBe(1000);
    });

    it('ignores non-printable keys', () => {
        const { command, typeAhead } = handleKey(
            mkCtx({ focusedId: 'alpha' }),
            'Shift',
        );
        expect(command).toEqual({ kind: 'noop' });
        // Shift is NOT type-ahead, so the buffer should be untouched.
        expect(typeAhead).toEqual({ text: '', lastKeyTime: 0 });
    });

    it('ignores control characters', () => {
        const { command } = handleKey(mkCtx({ focusedId: 'alpha' }), '\u0000');
        expect(command).toEqual({ kind: 'noop' });
    });

    it('finds a match starting from the very first visible item when buffer is empty and no focus', () => {
        const { command } = handleKey(mkCtx({ focusedId: null }), 'c');
        expect(command).toEqual({ kind: 'focus', id: 'cherry' });
    });
});

describe('handleKey — navigation keys reset type-ahead buffer', () => {
    it('ArrowDown clears an active type-ahead buffer', () => {
        const ctx = mkCtx({
            focusedId: 'alpha',
            typeAhead: { text: 'abc', lastKeyTime: 999 },
        });
        const { typeAhead } = handleKey(ctx, 'ArrowDown');
        expect(typeAhead).toEqual({ text: '', lastKeyTime: 0 });
    });

    it('Home clears the buffer', () => {
        const ctx = mkCtx({
            focusedId: 'cherry',
            typeAhead: { text: 'abc', lastKeyTime: 999 },
        });
        const { typeAhead } = handleKey(ctx, 'Home');
        expect(typeAhead).toEqual({ text: '', lastKeyTime: 0 });
    });
});

describe('handleKey — unhandled keys', () => {
    it('F1 is a noop and does not touch the buffer', () => {
        const ctx = mkCtx({
            focusedId: 'alpha',
            typeAhead: { text: 'hi', lastKeyTime: 500 },
            now: 600,
        });
        const { command, typeAhead } = handleKey(ctx, 'F1');
        expect(command).toEqual({ kind: 'noop' });
        expect(typeAhead).toEqual({ text: 'hi', lastKeyTime: 500 });
    });

    it('Escape is a noop (reserved for caller to handle e.g. dropdown close)', () => {
        const ctx = mkCtx({ focusedId: 'alpha' });
        const { command } = handleKey(ctx, 'Escape');
        expect(command).toEqual({ kind: 'noop' });
    });

    it('Tab is a noop (reserved for browser focus management)', () => {
        const ctx = mkCtx({ focusedId: 'alpha' });
        const { command } = handleKey(ctx, 'Tab');
        expect(command).toEqual({ kind: 'noop' });
    });
});

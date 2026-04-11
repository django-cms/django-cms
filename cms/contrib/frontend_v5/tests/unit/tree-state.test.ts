import { describe, expect, it } from 'vitest';
import { TreeState, type TreeNodeInit } from '../../src/modules/tree/state';

interface Payload {
    label: string;
}

const init = (id: string, parentId: string | null, label = id): TreeNodeInit<Payload> => ({
    id,
    parentId,
    data: { label },
});

/** Build a small fixture tree:
 *
 *   a
 *   ├─ a1
 *   │  └─ a1x
 *   └─ a2
 *   b
 *   └─ b1
 */
const buildFixture = () =>
    TreeState.from<Payload>([
        init('a', null),
        init('a1', 'a'),
        init('a1x', 'a1'),
        init('a2', 'a'),
        init('b', null),
        init('b1', 'b'),
    ]);

describe('TreeState.from', () => {
    it('builds a tree from a flat list', () => {
        const tree = buildFixture();
        expect(tree.size).toBe(6);
        expect(tree.rootIds()).toEqual(['a', 'b']);
        expect(tree.childrenOf('a')).toEqual(['a1', 'a2']);
        expect(tree.childrenOf('a1')).toEqual(['a1x']);
        expect(tree.childrenOf('b')).toEqual(['b1']);
    });

    it('preserves sibling order from the input list', () => {
        const tree = TreeState.from<Payload>([
            init('z', null),
            init('a', null),
            init('m', null),
        ]);
        expect(tree.rootIds()).toEqual(['z', 'a', 'm']);
    });

    it('accepts parents that come AFTER their children in the input', () => {
        const tree = TreeState.from<Payload>([
            init('child', 'parent'),
            init('parent', null),
        ]);
        expect(tree.rootIds()).toEqual(['parent']);
        expect(tree.childrenOf('parent')).toEqual(['child']);
    });

    it('throws on duplicate ids', () => {
        expect(() =>
            TreeState.from<Payload>([init('a', null), init('a', null)]),
        ).toThrow(/duplicate id "a"/);
    });

    it('throws when a parentId references an unknown id', () => {
        expect(() =>
            TreeState.from<Payload>([init('child', 'ghost')]),
        ).toThrow(/unknown parent "ghost"/);
    });

    it('throws on a cycle', () => {
        // Construct an evil pair where two nodes reference each other.
        // We can't go through `from()` directly because the second-pass
        // child wiring would catch it as "unknown parent" if we ordered
        // it differently — instead use two nodes that reference each
        // other (a→b, b→a, no roots).
        expect(() =>
            TreeState.from<Payload>([init('a', 'b'), init('b', 'a')]),
        ).toThrow(/cycle/);
    });
});

describe('TreeState reads', () => {
    const tree = buildFixture();

    it('has() / get()', () => {
        expect(tree.has('a1x')).toBe(true);
        expect(tree.has('nope')).toBe(false);
        expect(tree.get('a1x')?.data.label).toBe('a1x');
        expect(tree.get('nope')).toBeUndefined();
    });

    it('parentOf()', () => {
        expect(tree.parentOf('a1x')).toBe('a1');
        expect(tree.parentOf('a')).toBeNull();
        expect(tree.parentOf('nope')).toBeNull();
    });

    it('ancestorsOf() walks parent → root', () => {
        expect(tree.ancestorsOf('a1x')).toEqual(['a1', 'a']);
        expect(tree.ancestorsOf('a')).toEqual([]);
        expect(tree.ancestorsOf('nope')).toEqual([]);
    });

    it('descendantsOf() returns pre-order list', () => {
        expect(tree.descendantsOf('a')).toEqual(['a1', 'a1x', 'a2']);
        expect(tree.descendantsOf('a1x')).toEqual([]);
        expect(tree.descendantsOf('nope')).toEqual([]);
    });

    it('isDescendant() handles direct, indirect, and non-cases', () => {
        expect(tree.isDescendant('a', 'a1')).toBe(true);
        expect(tree.isDescendant('a', 'a1x')).toBe(true);
        expect(tree.isDescendant('a1', 'a1x')).toBe(true);
        expect(tree.isDescendant('a', 'a')).toBe(false); // self is not descendant
        expect(tree.isDescendant('a', 'b')).toBe(false);
        expect(tree.isDescendant('a1x', 'a')).toBe(false); // wrong direction
    });

    it('depth() reports tree depth from root', () => {
        expect(tree.depth('a')).toBe(0);
        expect(tree.depth('a1')).toBe(1);
        expect(tree.depth('a1x')).toBe(2);
        expect(tree.depth('b')).toBe(0);
    });

    it('childrenOf(null) returns roots', () => {
        expect(tree.childrenOf(null)).toEqual(['a', 'b']);
    });

    it('childrenOf() returns empty array for leaves and unknown ids', () => {
        expect(tree.childrenOf('a1x')).toEqual([]);
        expect(tree.childrenOf('nope')).toEqual([]);
    });
});

describe('TreeState.insert', () => {
    it('appends a new root when no index is given', () => {
        const tree = buildFixture();
        tree.insert(init('c', null));
        expect(tree.rootIds()).toEqual(['a', 'b', 'c']);
    });

    it('appends a new child of an existing parent', () => {
        const tree = buildFixture();
        tree.insert(init('a3', 'a'));
        expect(tree.childrenOf('a')).toEqual(['a1', 'a2', 'a3']);
    });

    it('inserts at the requested index', () => {
        const tree = buildFixture();
        tree.insert(init('a0', 'a'), 0);
        expect(tree.childrenOf('a')).toEqual(['a0', 'a1', 'a2']);
    });

    it('clamps an out-of-range positive index to the end', () => {
        const tree = buildFixture();
        tree.insert(init('aN', 'a'), 99);
        expect(tree.childrenOf('a')).toEqual(['a1', 'a2', 'aN']);
    });

    it('throws on negative index', () => {
        const tree = buildFixture();
        expect(() => tree.insert(init('x', 'a'), -1)).toThrow(/negative index/);
    });

    it('throws on duplicate id', () => {
        const tree = buildFixture();
        expect(() => tree.insert(init('a1', 'a'))).toThrow(/duplicate id "a1"/);
    });

    it('throws on unknown parent', () => {
        const tree = buildFixture();
        expect(() => tree.insert(init('x', 'ghost'))).toThrow(/unknown parent "ghost"/);
    });
});

describe('TreeState.remove', () => {
    it('removes a leaf and detaches it from its parent', () => {
        const tree = buildFixture();
        tree.remove('a1x');
        expect(tree.has('a1x')).toBe(false);
        expect(tree.childrenOf('a1')).toEqual([]);
        expect(tree.size).toBe(5);
    });

    it('removes a subtree (node + all descendants)', () => {
        const tree = buildFixture();
        tree.remove('a');
        expect(tree.has('a')).toBe(false);
        expect(tree.has('a1')).toBe(false);
        expect(tree.has('a1x')).toBe(false);
        expect(tree.has('a2')).toBe(false);
        expect(tree.rootIds()).toEqual(['b']);
        expect(tree.size).toBe(2);
    });

    it('is a no-op for unknown id', () => {
        const tree = buildFixture();
        tree.remove('nope');
        expect(tree.size).toBe(6);
    });
});

describe('TreeState.move', () => {
    it('moves to a different parent (append)', () => {
        const tree = buildFixture();
        tree.move('a1', 'b');
        expect(tree.parentOf('a1')).toBe('b');
        expect(tree.childrenOf('a')).toEqual(['a2']);
        expect(tree.childrenOf('b')).toEqual(['b1', 'a1']);
        // descendants come along for the ride:
        expect(tree.parentOf('a1x')).toBe('a1');
        expect(tree.depth('a1x')).toBe(2);
    });

    it('moves to a different parent at a specific index', () => {
        const tree = buildFixture();
        tree.move('a1', 'b', 0);
        expect(tree.childrenOf('b')).toEqual(['a1', 'b1']);
    });

    it('moves to root', () => {
        const tree = buildFixture();
        tree.move('a1x', null);
        expect(tree.parentOf('a1x')).toBeNull();
        expect(tree.rootIds()).toEqual(['a', 'b', 'a1x']);
        expect(tree.childrenOf('a1')).toEqual([]);
    });

    it('reorders within the same parent (forward)', () => {
        const tree = TreeState.from<Payload>([
            init('a', null),
            init('a1', 'a'),
            init('a2', 'a'),
            init('a3', 'a'),
            init('a4', 'a'),
        ]);
        // Move a1 (index 0) to index 2 in the post-move array.
        tree.move('a1', 'a', 2);
        expect(tree.childrenOf('a')).toEqual(['a2', 'a3', 'a1', 'a4']);
    });

    it('reorders within the same parent (backward)', () => {
        const tree = TreeState.from<Payload>([
            init('a', null),
            init('a1', 'a'),
            init('a2', 'a'),
            init('a3', 'a'),
            init('a4', 'a'),
        ]);
        // Move a4 (index 3) to index 0.
        tree.move('a4', 'a', 0);
        expect(tree.childrenOf('a')).toEqual(['a4', 'a1', 'a2', 'a3']);
    });

    it('moving to the end with undefined index works for same-parent', () => {
        const tree = TreeState.from<Payload>([
            init('a', null),
            init('a1', 'a'),
            init('a2', 'a'),
            init('a3', 'a'),
        ]);
        tree.move('a1', 'a');
        expect(tree.childrenOf('a')).toEqual(['a2', 'a3', 'a1']);
    });

    it('throws when moving a node into itself', () => {
        const tree = buildFixture();
        expect(() => tree.move('a', 'a')).toThrow(/into itself/);
    });

    it('throws when moving a node into its own descendant', () => {
        const tree = buildFixture();
        expect(() => tree.move('a', 'a1x')).toThrow(/into its own descendant/);
    });

    it('throws when moving an unknown id', () => {
        const tree = buildFixture();
        expect(() => tree.move('nope', 'a')).toThrow(/unknown id/);
    });

    it('throws when moving to an unknown parent', () => {
        const tree = buildFixture();
        expect(() => tree.move('a', 'ghost')).toThrow(/unknown parent/);
    });

    it('clamps a too-large index in the new parent', () => {
        const tree = buildFixture();
        tree.move('a1', 'b', 99);
        expect(tree.childrenOf('b')).toEqual(['b1', 'a1']);
    });
});

describe('TreeState.update', () => {
    it('replaces the data payload', () => {
        const tree = buildFixture();
        tree.update('a1', { label: 'renamed' });
        expect(tree.get('a1')?.data.label).toBe('renamed');
    });

    it('throws on unknown id', () => {
        const tree = buildFixture();
        expect(() => tree.update('nope', { label: 'x' })).toThrow(/unknown id/);
    });
});

describe('TreeState iteration', () => {
    it('iterPreOrder visits every node in depth-first sibling order', () => {
        const tree = buildFixture();
        expect([...tree.iterPreOrder()]).toEqual(['a', 'a1', 'a1x', 'a2', 'b', 'b1']);
    });

    it('visibleItems with empty expanded set returns roots only', () => {
        const tree = buildFixture();
        expect(tree.visibleItems(new Set())).toEqual(['a', 'b']);
    });

    it('visibleItems expands one branch', () => {
        const tree = buildFixture();
        expect(tree.visibleItems(new Set(['a']))).toEqual(['a', 'a1', 'a2', 'b']);
    });

    it('visibleItems expands a deep branch', () => {
        const tree = buildFixture();
        expect(tree.visibleItems(new Set(['a', 'a1']))).toEqual([
            'a',
            'a1',
            'a1x',
            'a2',
            'b',
        ]);
    });

    it('visibleItems with everything expanded equals iterPreOrder', () => {
        const tree = buildFixture();
        const allIds = new Set([...tree.iterPreOrder()]);
        expect(tree.visibleItems(allIds)).toEqual([...tree.iterPreOrder()]);
    });
});

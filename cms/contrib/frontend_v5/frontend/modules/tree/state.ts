/*
 * Tree state model.
 *
 * A small, framework-agnostic data structure for the parent/child
 * relationships behind the pagetree and structureboard. Owns ONLY the
 * structural concerns: which node is whose parent, sibling order, and
 * safe mutation under invariants. Rendering, expand state, selection,
 * keyboard navigation, and drag-and-drop are layered on top by other
 * modules — none of those concerns leak into here.
 *
 * Each node carries an opaque `data: T` payload that the consumer owns
 * (label, icon, lazy-load status, plugin type, etc.). This module never
 * inspects it.
 *
 * Node IDs are plain strings. They must be unique across the whole tree.
 * The model rejects mutations that would create cycles, duplicate IDs,
 * or dangling parent references — all such errors are thrown synchronously
 * with descriptive messages.
 */

export type NodeId = string;

export interface TreeNode<T> {
    readonly id: NodeId;
    readonly parentId: NodeId | null;
    readonly data: T;
    readonly childIds: readonly NodeId[];
}

/** Shape used by `TreeState.from()` to hydrate from a flat list. */
export interface TreeNodeInit<T> {
    id: NodeId;
    parentId: NodeId | null;
    data: T;
}

interface InternalNode<T> {
    id: NodeId;
    parentId: NodeId | null;
    data: T;
    childIds: NodeId[];
}

export class TreeState<T> {
    private readonly nodes = new Map<NodeId, InternalNode<T>>();
    private readonly roots: NodeId[] = [];

    /**
     * Build a TreeState from a flat list of nodes. Order does not matter
     * (parents may appear before or after their children). The list must
     * be self-consistent: no duplicate IDs, every non-null parentId must
     * reference an entry in the same list, and the resulting graph must
     * be a forest (no cycles).
     */
    static from<T>(items: readonly TreeNodeInit<T>[]): TreeState<T> {
        const tree = new TreeState<T>();

        for (const item of items) {
            if (tree.nodes.has(item.id)) {
                throw new Error(`TreeState.from: duplicate id "${item.id}"`);
            }
            tree.nodes.set(item.id, {
                id: item.id,
                parentId: item.parentId,
                data: item.data,
                childIds: [],
            });
        }

        // Second pass: wire up child arrays in input order so siblings
        // appear in the same order as the input list.
        for (const item of items) {
            if (item.parentId === null) {
                tree.roots.push(item.id);
                continue;
            }
            const parent = tree.nodes.get(item.parentId);
            if (!parent) {
                throw new Error(
                    `TreeState.from: node "${item.id}" references unknown parent "${item.parentId}"`,
                );
            }
            parent.childIds.push(item.id);
        }

        // Cycle detection: walk every root and ensure we visit every node
        // exactly once. If a cycle exists, some nodes are unreachable from
        // any root, so the visited count won't match the node count.
        const visited = new Set<NodeId>();
        const stack: NodeId[] = [...tree.roots];
        while (stack.length > 0) {
            const id = stack.pop()!;
            if (visited.has(id)) {
                throw new Error(`TreeState.from: cycle detected at "${id}"`);
            }
            visited.add(id);
            const node = tree.nodes.get(id)!;
            stack.push(...node.childIds);
        }
        if (visited.size !== tree.nodes.size) {
            throw new Error('TreeState.from: cycle or disconnected component detected');
        }

        return tree;
    }

    // ---------- reads ----------

    get size(): number {
        return this.nodes.size;
    }

    has(id: NodeId): boolean {
        return this.nodes.has(id);
    }

    get(id: NodeId): TreeNode<T> | undefined {
        return this.nodes.get(id);
    }

    /** IDs of root-level nodes (parentId === null), in sibling order. */
    rootIds(): readonly NodeId[] {
        return this.roots;
    }

    /**
     * Children of a node, in sibling order. Pass null to get roots.
     * Returns an empty array for leaves and for unknown ids — callers
     * that need to distinguish "no children" from "no such node" should
     * use `has()` first.
     */
    childrenOf(parentId: NodeId | null): readonly NodeId[] {
        if (parentId === null) return this.roots;
        return this.nodes.get(parentId)?.childIds ?? [];
    }

    parentOf(id: NodeId): NodeId | null {
        return this.nodes.get(id)?.parentId ?? null;
    }

    /** Ancestors from immediate parent up to the root (root is last). */
    ancestorsOf(id: NodeId): NodeId[] {
        const out: NodeId[] = [];
        let cur = this.nodes.get(id)?.parentId ?? null;
        while (cur !== null) {
            out.push(cur);
            cur = this.nodes.get(cur)?.parentId ?? null;
        }
        return out;
    }

    /** Pre-order list of all descendants of `id` (does NOT include `id`). */
    descendantsOf(id: NodeId): NodeId[] {
        const out: NodeId[] = [];
        const node = this.nodes.get(id);
        if (!node) return out;
        const walk = (parentId: NodeId) => {
            for (const childId of this.nodes.get(parentId)!.childIds) {
                out.push(childId);
                walk(childId);
            }
        };
        walk(id);
        return out;
    }

    isDescendant(ancestorId: NodeId, candidateId: NodeId): boolean {
        let cur = this.nodes.get(candidateId)?.parentId ?? null;
        while (cur !== null) {
            if (cur === ancestorId) return true;
            cur = this.nodes.get(cur)?.parentId ?? null;
        }
        return false;
    }

    /** 0 for root nodes, 1 for direct children of roots, etc. */
    depth(id: NodeId): number {
        return this.ancestorsOf(id).length;
    }

    // ---------- mutations ----------

    /**
     * Insert a new node under `parentId` (null = root) at the given
     * sibling index. Index defaults to "append at end". Out-of-range
     * positive indices are clamped to the end; negative indices throw.
     */
    insert(init: TreeNodeInit<T>, index?: number): void {
        if (this.nodes.has(init.id)) {
            throw new Error(`TreeState.insert: duplicate id "${init.id}"`);
        }
        if (init.parentId !== null && !this.nodes.has(init.parentId)) {
            throw new Error(
                `TreeState.insert: unknown parent "${init.parentId}" for "${init.id}"`,
            );
        }

        const node: InternalNode<T> = {
            id: init.id,
            parentId: init.parentId,
            data: init.data,
            childIds: [],
        };
        this.nodes.set(init.id, node);

        const siblings = init.parentId === null ? this.roots : this.nodes.get(init.parentId)!.childIds;
        const pos = this.resolveInsertIndex(siblings.length, index);
        siblings.splice(pos, 0, init.id);
    }

    /**
     * Remove a node and all of its descendants. No-op if `id` is unknown.
     */
    remove(id: NodeId): void {
        const node = this.nodes.get(id);
        if (!node) return;

        // Detach from parent's child list (or roots).
        const siblings = node.parentId === null ? this.roots : this.nodes.get(node.parentId)!.childIds;
        const pos = siblings.indexOf(id);
        if (pos !== -1) siblings.splice(pos, 1);

        // Drop the subtree from the node map.
        const toDelete = [id, ...this.descendantsOf(id)];
        for (const victim of toDelete) {
            this.nodes.delete(victim);
        }
    }

    /**
     * Move a node to a new parent (null = root) and a new sibling index.
     * Index defaults to "append at end" of the new parent's children.
     *
     * Throws on cycle attempts (moving a node into itself or any of its
     * descendants) and on unknown ids. A move with the same parent and
     * the same effective index is a no-op.
     */
    move(id: NodeId, newParentId: NodeId | null, newIndex?: number): void {
        const node = this.nodes.get(id);
        if (!node) {
            throw new Error(`TreeState.move: unknown id "${id}"`);
        }
        if (newParentId !== null && !this.nodes.has(newParentId)) {
            throw new Error(`TreeState.move: unknown parent "${newParentId}"`);
        }
        if (newParentId === id) {
            throw new Error(`TreeState.move: cannot move "${id}" into itself`);
        }
        if (newParentId !== null && this.isDescendant(id, newParentId)) {
            throw new Error(
                `TreeState.move: cannot move "${id}" into its own descendant "${newParentId}"`,
            );
        }

        const oldSiblings = node.parentId === null ? this.roots : this.nodes.get(node.parentId)!.childIds;
        const newSiblings = newParentId === null ? this.roots : this.nodes.get(newParentId)!.childIds;
        const oldPos = oldSiblings.indexOf(id);

        // newIndex is interpreted as the desired POST-move position in
        // the new sibling array. When moving within the same parent we
        // resolve the index against (length - 1) because the node will be
        // briefly removed before reinsertion.
        const postRemoveLength =
            oldSiblings === newSiblings ? newSiblings.length - 1 : newSiblings.length;
        const targetPos = this.resolveInsertIndex(postRemoveLength, newIndex);

        if (oldPos !== -1) oldSiblings.splice(oldPos, 1);
        newSiblings.splice(targetPos, 0, id);
        node.parentId = newParentId;
    }

    /** Replace the data payload of an existing node. */
    update(id: NodeId, data: T): void {
        const node = this.nodes.get(id);
        if (!node) {
            throw new Error(`TreeState.update: unknown id "${id}"`);
        }
        node.data = data;
    }

    // ---------- iteration ----------

    /**
     * Iterate every node in pre-order (depth-first, sibling order). Yields
     * IDs only — call `get(id)` if you need the node payload.
     */
    *iterPreOrder(): IterableIterator<NodeId> {
        const stack: NodeId[] = [...this.roots].reverse();
        while (stack.length > 0) {
            const id = stack.pop()!;
            yield id;
            const node = this.nodes.get(id)!;
            for (let i = node.childIds.length - 1; i >= 0; i--) {
                stack.push(node.childIds[i]!);
            }
        }
    }

    /**
     * Pre-order list of nodes that should be visible in the UI given the
     * caller's expand state: a node is visible iff all its ancestors are
     * in `expandedIds`. Roots are always visible. Used by keyboard-nav to
     * compute "next/prev visible" without re-walking the tree on every
     * arrow press.
     */
    visibleItems(expandedIds: ReadonlySet<NodeId>): NodeId[] {
        const out: NodeId[] = [];
        const walk = (id: NodeId) => {
            out.push(id);
            if (!expandedIds.has(id)) return;
            const node = this.nodes.get(id)!;
            for (const childId of node.childIds) walk(childId);
        };
        for (const rootId of this.roots) walk(rootId);
        return out;
    }

    // ---------- internals ----------

    private resolveInsertIndex(siblingCount: number, requested: number | undefined): number {
        if (requested === undefined) return siblingCount;
        if (requested < 0) {
            throw new Error(`TreeState: negative index ${requested} not allowed`);
        }
        return Math.min(requested, siblingCount);
    }
}

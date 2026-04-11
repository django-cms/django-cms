/*
 * Keyboard navigation for tree widgets per the WAI-ARIA tree pattern.
 * https://www.w3.org/WAI/ARIA/apg/patterns/treeview/
 *
 * This is a PURE FUNCTION over tree state. It takes a context + a key
 * name and returns a *command* describing what the caller should do.
 * The caller is responsible for applying the command (updating focused
 * id, expand set, activating a node, etc.).
 *
 * Why pure?
 *   - Deterministic → exhaustively testable without a DOM.
 *   - Decouples decision from mutation → easy to reuse from pagetree
 *     AND structureboard without forcing a shared state object.
 *   - Easy to unit-test every spec case with a table of inputs.
 *
 * Scope (v1, single-selection tree):
 *   - Focus nav:  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Home, End
 *   - Activation: Enter, Space
 *   - Type-ahead: single- and multi-char; buffer resets after 500ms;
 *                 wraps around; case-insensitive.
 *
 * NOT in scope (add if/when pagetree or structureboard need it):
 *   - Multi-select (Shift+Arrow)
 *   - Asterisk ("*" expands all siblings at focus level)
 *   - Checkbox tree semantics
 */

import type { NodeId } from './state';

/**
 * The subset of TreeState<T> methods this module depends on. Using a
 * structural interface keeps keyboard-nav decoupled from the concrete
 * TreeState class — TreeState<T> satisfies it for any T.
 */
export interface TreeLike {
    has(id: NodeId): boolean;
    parentOf(id: NodeId): NodeId | null;
    childrenOf(parentId: NodeId | null): readonly NodeId[];
    visibleItems(expandedIds: ReadonlySet<NodeId>): NodeId[];
}

export type KeyCommand =
    | { kind: 'noop' }
    | { kind: 'focus'; id: NodeId }
    | { kind: 'expand'; id: NodeId }
    | { kind: 'collapse'; id: NodeId }
    | { kind: 'activate'; id: NodeId };

/**
 * Caller-owned type-ahead buffer. Pass the SAME object across calls to
 * accumulate multi-character searches ("ap" finds "apple" after "applause"
 * depending on cursor). Reset automatically after TYPEAHEAD_RESET_MS of
 * inactivity.
 */
export interface TypeAheadBuffer {
    text: string;
    /** Wall-clock ms of last keystroke, from `performance.now()` or Date.now(). */
    lastKeyTime: number;
}

export const TYPEAHEAD_RESET_MS = 500;

export interface KeyContext {
    tree: TreeLike;
    expandedIds: ReadonlySet<NodeId>;
    focusedId: NodeId | null;
    /** Called to retrieve the display label used for type-ahead matching. */
    getLabel: (id: NodeId) => string;
    typeAhead: TypeAheadBuffer;
    /** Current wall-clock ms. Injected so tests can be deterministic. */
    now: number;
}

export interface KeyResult {
    command: KeyCommand;
    /** The updated type-ahead buffer. Callers replace theirs with this value. */
    typeAhead: TypeAheadBuffer;
}

const NOOP: KeyCommand = { kind: 'noop' };

function isExpandable(tree: TreeLike, id: NodeId): boolean {
    return tree.childrenOf(id).length > 0;
}

function isExpanded(ctx: KeyContext, id: NodeId): boolean {
    return ctx.expandedIds.has(id);
}

/**
 * Main entry point. Takes a key context and the `event.key` string of a
 * keydown event, returns a command + the new type-ahead buffer.
 *
 * Callers should `event.preventDefault()` iff the returned command is
 * NOT `noop` — that way we don't hijack keystrokes we didn't handle.
 */
export function handleKey(ctx: KeyContext, key: string): KeyResult {
    // Short-circuit: empty tree. Nothing to do on any key.
    if (ctx.tree.visibleItems(ctx.expandedIds).length === 0) {
        return { command: NOOP, typeAhead: ctx.typeAhead };
    }

    // Navigation keys don't touch the type-ahead buffer, but they DO reset
    // it implicitly — a user pressing an arrow key has stopped searching.
    // Exception: Enter and Space don't reset either (no reason to).
    switch (key) {
        case 'ArrowDown':
            return navCmd(ctx, moveDown(ctx));
        case 'ArrowUp':
            return navCmd(ctx, moveUp(ctx));
        case 'ArrowRight':
            return navCmd(ctx, moveRight(ctx));
        case 'ArrowLeft':
            return navCmd(ctx, moveLeft(ctx));
        case 'Home':
            return navCmd(ctx, moveHome(ctx));
        case 'End':
            return navCmd(ctx, moveEnd(ctx));
        case 'Enter':
        case ' ':
        case 'Spacebar': // legacy IE/old-Edge key name
            return { command: activate(ctx), typeAhead: ctx.typeAhead };
        default:
            // Type-ahead: accept printable single characters. Ignore
            // modifiers, function keys, meta keys, etc.
            if (isPrintableChar(key)) {
                return handleTypeAhead(ctx, key);
            }
            return { command: NOOP, typeAhead: ctx.typeAhead };
    }
}

function navCmd(ctx: KeyContext, command: KeyCommand): KeyResult {
    // Navigation resets the type-ahead buffer (user stopped searching).
    const typeAhead: TypeAheadBuffer = { text: '', lastKeyTime: 0 };
    return { command, typeAhead };
}

function isPrintableChar(key: string): boolean {
    // `event.key` is the printed character for printable keys, or a long
    // name like "ArrowDown" / "Shift" / "F1" for non-printable. We accept
    // exactly 1-character values that aren't whitespace/control.
    return key.length === 1 && key >= ' ';
}

// ---------- ArrowDown: next visible ----------
function moveDown(ctx: KeyContext): KeyCommand {
    const visible = ctx.tree.visibleItems(ctx.expandedIds);
    if (ctx.focusedId === null) {
        return { kind: 'focus', id: visible[0]! };
    }
    const idx = visible.indexOf(ctx.focusedId);
    if (idx === -1) return { kind: 'focus', id: visible[0]! };
    if (idx === visible.length - 1) return NOOP;
    return { kind: 'focus', id: visible[idx + 1]! };
}

// ---------- ArrowUp: previous visible ----------
function moveUp(ctx: KeyContext): KeyCommand {
    const visible = ctx.tree.visibleItems(ctx.expandedIds);
    if (ctx.focusedId === null) {
        return { kind: 'focus', id: visible[0]! };
    }
    const idx = visible.indexOf(ctx.focusedId);
    if (idx === -1) return { kind: 'focus', id: visible[0]! };
    if (idx === 0) return NOOP;
    return { kind: 'focus', id: visible[idx - 1]! };
}

// ---------- ArrowRight ----------
// Closed parent → expand (focus stays)
// Open parent   → focus first child
// Leaf          → no-op
function moveRight(ctx: KeyContext): KeyCommand {
    if (ctx.focusedId === null || !ctx.tree.has(ctx.focusedId)) return NOOP;
    if (!isExpandable(ctx.tree, ctx.focusedId)) return NOOP;
    if (!isExpanded(ctx, ctx.focusedId)) {
        return { kind: 'expand', id: ctx.focusedId };
    }
    const firstChild = ctx.tree.childrenOf(ctx.focusedId)[0];
    if (!firstChild) return NOOP;
    return { kind: 'focus', id: firstChild };
}

// ---------- ArrowLeft ----------
// Open parent         → collapse (focus stays)
// Leaf/closed + parent → focus parent
// Root leaf/closed    → no-op
function moveLeft(ctx: KeyContext): KeyCommand {
    if (ctx.focusedId === null || !ctx.tree.has(ctx.focusedId)) return NOOP;
    if (isExpandable(ctx.tree, ctx.focusedId) && isExpanded(ctx, ctx.focusedId)) {
        return { kind: 'collapse', id: ctx.focusedId };
    }
    const parent = ctx.tree.parentOf(ctx.focusedId);
    if (parent === null) return NOOP;
    return { kind: 'focus', id: parent };
}

// ---------- Home / End ----------
function moveHome(ctx: KeyContext): KeyCommand {
    const visible = ctx.tree.visibleItems(ctx.expandedIds);
    const first = visible[0];
    return first !== undefined ? { kind: 'focus', id: first } : NOOP;
}

function moveEnd(ctx: KeyContext): KeyCommand {
    const visible = ctx.tree.visibleItems(ctx.expandedIds);
    const last = visible[visible.length - 1];
    return last !== undefined ? { kind: 'focus', id: last } : NOOP;
}

// ---------- Enter / Space ----------
// On an expandable node: toggle expansion.
// On a leaf: activate (caller decides what that means — open, select, etc.).
function activate(ctx: KeyContext): KeyCommand {
    if (ctx.focusedId === null || !ctx.tree.has(ctx.focusedId)) return NOOP;
    if (isExpandable(ctx.tree, ctx.focusedId)) {
        return isExpanded(ctx, ctx.focusedId)
            ? { kind: 'collapse', id: ctx.focusedId }
            : { kind: 'expand', id: ctx.focusedId };
    }
    return { kind: 'activate', id: ctx.focusedId };
}

// ---------- Type-ahead ----------
function handleTypeAhead(ctx: KeyContext, char: string): KeyResult {
    // Reset buffer if too much time has passed since the last keystroke.
    const timedOut = ctx.now - ctx.typeAhead.lastKeyTime > TYPEAHEAD_RESET_MS;
    const nextText = (timedOut ? '' : ctx.typeAhead.text) + char;
    const newBuffer: TypeAheadBuffer = {
        text: nextText,
        lastKeyTime: ctx.now,
    };

    const visible = ctx.tree.visibleItems(ctx.expandedIds);
    if (visible.length === 0) {
        return { command: NOOP, typeAhead: newBuffer };
    }

    const needle = nextText.toLowerCase();

    // Start searching from the item AFTER the currently-focused one; if
    // no match is found by end of list, wrap to the beginning. This is
    // what makes repeated presses of the same character cycle through
    // matches ("a" → "apple", "a" again → "apricot", "a" again → "apple").
    //
    // HOWEVER: when the buffer is more than one character (multi-char
    // search like "ap"), start from the currently-focused item INSTEAD —
    // otherwise typing "apple" would skip the first match.
    const startIdx =
        nextText.length === 1 && ctx.focusedId !== null
            ? (visible.indexOf(ctx.focusedId) + 1) % visible.length
            : 0;

    for (let i = 0; i < visible.length; i++) {
        const idx = (startIdx + i) % visible.length;
        const id = visible[idx]!;
        const label = ctx.getLabel(id).toLowerCase();
        if (label.startsWith(needle)) {
            return { command: { kind: 'focus', id }, typeAhead: newBuffer };
        }
    }

    // No match — still update the buffer (so further chars compound),
    // but don't change focus.
    return { command: NOOP, typeAhead: newBuffer };
}

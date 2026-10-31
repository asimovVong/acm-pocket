import test from 'node:test';
import assert from 'node:assert/strict';
let hydrateState;
try { ({ hydrateState } = await import('../state.mjs')); } catch {}
function hydrate(primary, legacy) {
  assert.equal(typeof hydrateState, 'function', 'Draft migration is missing');
  return hydrateState(primary, legacy, ['209', '42', '3', '206']);
}
test('migrates existing 209 and free drafts without changing code or expected output', () => {
  const legacy = { mode: 'free', drafts: { '209': { code: 'my solution', stdin: '6 7', expected: '', compare: false }, free: { code: 'print(6)', stdin: '1 2 3', expected: '6', compare: true } } };
  const state = hydrate(null, legacy);
  assert.equal(state.mode, 'free');
  assert.equal(state.drafts['209'].code, 'my solution');
  assert.equal(state.drafts['209'].expected, '');
  assert.equal(state.drafts['209'].compare, false);
  assert.equal(state.drafts.free.stdin, '1 2 3');
  assert.equal(legacy.mode, 'free');
});
test('new multi-problem drafts win over legacy and completion can stay unmarked', () => {
  const draft = { code: 'new', stdin: 'a', expected: '1', compare: true };
  const state = hydrate({ mode: '3', lastProblem: '3', drafts: { '3': draft }, completed: {} }, { drafts: { '3': { ...draft, code: 'old' } } });
  assert.equal(state.mode, '3');
  assert.equal(state.drafts['3'].code, 'new');
  assert.deepEqual(state.completed, {});
});
test('malformed state falls back without preventing startup or losing valid drafts', () => {
  const state = hydrate({ mode: 'unknown', drafts: { '209': { code: 'keep', stdin: '', expected: '' }, '3': { code: 17 } }, completed: { '42': true, '3': 'yes' } }, null);
  assert.equal(state.mode, '209');
  assert.equal(state.drafts['209'].code, 'keep');
  assert.equal(state.drafts['3'], undefined);
  assert.deepEqual(state.completed, { '42': true });
});

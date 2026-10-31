import test from 'node:test';
import assert from 'node:assert/strict';

let compareOutput;
try { ({ compareOutput } = await import('../judge.mjs')); } catch {}
function compare(actual, expected, rule = 'tokens', stdin = '') {
  assert.equal(typeof compareOutput, 'function', 'Output comparator is missing');
  return compareOutput(actual, expected, rule, stdin);
}

test('ACM whitespace is ignored, but token contents are preserved', () => {
  assert.equal(compare('1  2\r\n3\n', '1\n2 3').pass, true);
  assert.equal(compare('12\n', '1 2').pass, false);
  assert.equal(compare('2.0', '2').pass, false);
});
test('JSON compares values while preserving ordered sequences', () => {
  assert.equal(compare('[1,2]', '[1, 2]', 'json').pass, true);
  assert.equal(compare('[2,1]', '[1,2]', 'json').pass, false);
  assert.equal(compare("['a']", '["a"]', 'json').pass, false);
});
test('solution collections allow outer order but preserve partition and board order', () => {
  assert.equal(compare('[["aa"],["a","a"]]', '[["a","a"],["aa"]]', 'unordered').pass, true);
  assert.equal(compare('[["b","aa"]]', '[["aa","b"]]', 'unordered').pass, false);
  assert.equal(compare('[[1],[1]]', '[[1]]', 'unordered').pass, false);
});
test('combinations ignore inner and outer order, without dropping duplicates', () => {
  assert.equal(compare('[[3,1],[2,1]]', '[[1,2],[1,3]]', 'unordered-nested').pass, true);
  assert.equal(compare('[[1,1]]', '[[1]]', 'unordered-nested').pass, false);
  assert.equal(compare('[1,2]', '[[1,2]]', 'unordered-nested').pass, false);
});
test('peak finder accepts any true peak and rejects invalid or extra indices', () => {
  const stdin = '7\n1 2 1 3 5 6 4\n';
  assert.equal(compare('1', '5', 'peak', stdin).pass, true);
  assert.equal(compare('5', '5', 'peak', stdin).pass, true);
  assert.equal(compare('0', '5', 'peak', stdin).pass, false);
  assert.equal(compare('7', '5', 'peak', stdin).pass, false);
  assert.equal(compare('1 5', '5', 'peak', stdin).pass, false);
  assert.equal(compare('0', '0', 'peak', '1\n9').pass, true);
  assert.equal(compare('1', '1', 'peak', '7\n1 2').pass, false);
});
test('reports the first mismatch including missing output', () => {
  assert.deepEqual(compare('1 8', '1 2'), { pass: false, index: 1, actual: '8', expected: '2' });
  assert.deepEqual(compare('', '2'), { pass: false, index: 0, actual: null, expected: '2' });
  assert.equal(compare('', '\n ').pass, true);
  assert.equal(compare('debug\n2', '2').pass, false);
});

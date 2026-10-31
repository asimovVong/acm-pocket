import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { compareOutput } from '../judge.mjs';

const root = fileURLToPath(new URL('..', import.meta.url));
const read = name => readFile(new URL(`../data/${name}.json`, import.meta.url), 'utf8').then(JSON.parse);
const questions = (await Promise.all(['arrays', 'structures', 'dp'].map(read))).flat();
const references = (await Promise.all(['arrays', 'structures', 'dp'].map(async name => {
  try { return await read(`references-${name}`); } catch { return []; }
}))).flat();

test('each course question has a complete reference with a matching primary source and explained imports', () => {
  assert.deepEqual(references.map(r => r.id).sort(), questions.map(q => q.id).sort());
  for (const reference of references) {
    const question = questions.find(q => q.id === reference.id);
    assert.equal(reference.author, '灵茶山艾府');
    assert.ok(reference.sourceUrl.startsWith(question.url.replace(/\/$/, '') + '/solution'), reference.id);
    for (const field of ['sourceTitle', 'variant', 'code', 'note']) assert.ok(reference[field]?.trim(), `${reference.id}.${field}`);
    assert.ok(reference.imports.length > 0, reference.id);
    for (const item of reference.imports) {
      assert.ok(reference.code.includes(item.code), `${reference.id}: ${item.code}`);
      assert.ok(item.purpose.trim(), reference.id);
    }
  }
});

test('complete references execute against every fixed fixture using the real ACM runner and comparator', () => {
  assert.equal(references.length, questions.length, 'References are missing');
  const output = execFileSync('python3', ['tests/run_references.py'], { cwd: root, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024, timeout: 90000 });
  const results = JSON.parse(output);
  assert.equal(results.length, questions.reduce((sum, q) => sum + q.cases.length, 0));
  for (const item of results) {
    const question = questions.find(q => q.id === item.id);
    const fixture = question.cases[item.index];
    assert.equal(item.error, null, `${item.id} ${fixture.name}: ${item.error}`);
    const verdict = compareOutput(item.stdout, fixture.expected, question.judge, fixture.stdin);
    assert.equal(verdict.pass, true, `${item.id} ${fixture.name}: ${JSON.stringify(verdict)}`);
  }
});

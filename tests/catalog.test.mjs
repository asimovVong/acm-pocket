import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { filterProblems } from '../catalog.mjs';

const read = name => readFile(new URL(`../data/${name}.json`, import.meta.url), 'utf8').then(JSON.parse);
const questions = (await Promise.all(['arrays', 'structures', 'dp'].map(read))).flat();
const manifest = await read('source-manifest');

test('every primary course problem is present once, with matching source and episodes', () => {
  assert.equal(new Set(questions.map(q => q.id)).size, questions.length);
  assert.deepEqual(questions.map(q => q.id).sort(), [...new Set(manifest.map(q => q.id))].sort());
  for (const question of questions) {
    const sources = manifest.filter(source => source.id === question.id);
    assert.equal(question.url, sources[0].url, question.id);
    assert.deepEqual(question.episodes, sources.map(source => source.episode), question.id);
  }
});
test('every selectable problem has usable I/O instructions, a starter, and valid fixed fixtures', () => {
  for (const question of questions) {
    for (const field of ['title', 'topic', 'statement', 'inputFormat', 'outputFormat', 'starter']) assert.ok(typeof question[field] === 'string' && question[field].trim(), `${question.id}.${field}`);
    assert.ok(['tokens', 'json', 'unordered', 'unordered-nested', 'peak'].includes(question.judge), question.id);
    assert.ok(question.cases.length >= 3, question.id);
    for (const fixture of question.cases) {
      assert.equal(typeof fixture.stdin, 'string', question.id);
      assert.equal(typeof fixture.expected, 'string', question.id);
      if (['json', 'unordered', 'unordered-nested'].includes(question.judge)) JSON.parse(fixture.expected);
    }
  }
});
test('search, topic and unfinished filters combine without hiding an unmarked problem', () => {
  const examples = [
    { id: '42', title: '接雨水', topic: '双指针', episode: 2 },
    { id: '209', title: '长度最小的子数组', topic: '滑动窗口', episode: 3 },
    { id: '3', title: '无重复字符的最长子串', topic: '滑动窗口', episode: 3 },
  ];
  assert.deepEqual(filterProblems(examples, ' 42 ').map(p => p.id), ['42']);
  assert.deepEqual(filterProblems(examples, '子', '滑动窗口', true, { '209': true }).map(p => p.id), ['3']);
  assert.deepEqual(filterProblems(examples, '不存在'), []);
  assert.equal(filterProblems(examples, '', '', true, { '42': false }).length, 3);
});

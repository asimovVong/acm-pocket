import { compareOutput } from './judge.mjs';
import { loadCatalog, filterProblems } from './catalog.mjs';
import { hydrateState } from './state.mjs';
import { loadReferences } from './references.mjs';

const $ = id => document.getElementById(id);
const elements = Object.fromEntries(['code', 'stdin', 'expected', 'compare', 'run', 'run-all', 'stop', 'runtime-status', 'runtime-dot', 'retry', 'save-status', 'result-summary', 'result-details', 'result-time'].map(id => [id, $(id)]));
let problems;
try { problems = await loadCatalog(); }
catch (error) {
  elements['runtime-status'].textContent = '题库加载失败';
  elements['runtime-dot'].className = 'runtime-dot error';
  elements.retry.hidden = false;
  elements.retry.addEventListener('click', () => location.reload());
  elements['result-summary'].textContent = String(error);
  throw error;
}
const problemById = new Map(problems.map(problem => [problem.id, problem]));
const freeTemplate = `import sys

def solve():
    # 示例：读取所有整数并输出它们的和
    nums = list(map(int, sys.stdin.read().split()))
    print(sum(nums))

if __name__ == '__main__':
    solve()
`;
const storageKey = 'acm-practice-v2';
function readSaved(key) {
  try { return JSON.parse(localStorage.getItem(key) || 'null'); }
  catch { return null; }
}
let { mode, lastProblem, drafts, completed } = hydrateState(readSaved(storageKey), readSaved('acm-practice-v1'), problems.map(p => p.id));
const currentProblem = () => problemById.get(mode);
const currentTemplate = () => currentProblem()?.starter || freeTemplate;
let references = new Map();
let referenceError = '';
let showReference = true;
try { showReference = localStorage.getItem('acm-reference-visible') !== 'false'; } catch {}
const currentReference = () => references.get(mode);
const defaultDraft = id => {
  const problem = problemById.get(id);
  return { code: problem?.starter || freeTemplate, stdin: problem?.cases[0].stdin ?? '1 2 3\n', expected: problem?.cases[0].expected ?? '6', compare: true };
};

let worker = null;
let ready = false;
let busy = false;
let requestId = 0;
let pending = null;
let bootTimer;
let pythonVersion = '3';
let stopped = false;
let resultDraft = null;

function updateControls() {
  elements.run.disabled = !ready || busy;
  elements['run-all'].disabled = !ready || busy;
  elements.stop.hidden = !busy;
  $('mode-bank').disabled = busy;
  $('open-catalog').disabled = busy;
  $('toggle-complete').disabled = busy;
  const index = problems.findIndex(problem => problem.id === mode);
  $('previous-problem').disabled = busy || index <= 0;
  $('next-problem').disabled = busy || index >= problems.length - 1;
  $('mode-free').disabled = busy;
  $('template').disabled = busy;
  elements.code.readOnly = busy;
  elements.stdin.readOnly = busy;
  elements.expected.readOnly = busy;
  elements.compare.disabled = busy;
  for (const id of ['run-reference', 'verify-reference']) $(id).disabled = busy || !ready || !currentReference();
  for (const id of ['copy-reference', 'download-reference']) $(id).disabled = !currentReference();
  document.querySelectorAll('[data-sample]').forEach(button => { button.disabled = busy; });
}

function runtimeStatus(text, state) {
  elements['runtime-status'].textContent = text;
  elements['runtime-dot'].className = `runtime-dot ${state || ''}`;
}

function finishPending(result) {
  if (!pending) return;
  const current = pending;
  pending = null;
  clearTimeout(current.timer);
  current.resolve(result);
}

function killWorker() {
  worker?.terminate();
  worker = null;
  ready = false;
  clearTimeout(bootTimer);
}

function initializationFailed(message) {
  killWorker();
  runtimeStatus('Python 加载失败', 'error');
  elements.retry.hidden = false;
  setSummary('fail', 'Python 还没准备好', '请检查网络后点击右上角「重新加载」。你的代码仍然保留。');
  elements['result-details'].replaceChildren();
  addOutput(elements['result-details'], '加载详情', message, true);
  updateControls();
}

function initializeRuntime() {
  killWorker();
  elements.retry.hidden = true;
  runtimeStatus('正在加载 Python…', 'loading');
  updateControls();
  const current = new Worker('./worker.js', { type: 'module' });
  worker = current;
  bootTimer = setTimeout(() => {
    if (worker === current) initializationFailed('运行环境加载超时。首次加载需要下载 Python，请稍后重试。');
  }, 90000);
  current.onmessage = ({ data }) => {
    if (worker !== current) return;
    if (data.type === 'ready') {
      clearTimeout(bootTimer);
      ready = true;
      pythonVersion = data.version;
      runtimeStatus(`Python ${pythonVersion} 已就绪`);
      updateControls();
    } else if (data.type === 'init-error') {
      initializationFailed(data.error);
    } else if (pending && data.id === pending.id) {
      if (data.type === 'started') {
        clearTimeout(pending.timer);
        pending.timer = setTimeout(() => {
          killWorker();
          finishPending({ stdout: '', stderr: '', error: '单组运行超过 3 秒。请检查死循环、指针是否移动，或降低算法复杂度。', kind: 'timeout', elapsed: 3000 });
        }, 3000);
      } else if (data.type === 'result') {
        finishPending(data);
      }
    }
  };
  current.onerror = event => {
    event.preventDefault();
    if (worker !== current) return;
    const message = event.message || 'Python 运行环境意外退出，请重新加载。';
    if (pending) {
      killWorker();
      finishPending({ stdout: '', stderr: '', error: message, kind: 'crash', elapsed: 0 });
    } else {
      initializationFailed(message);
    }
  };
}

function execute(code, stdin) {
  return new Promise(resolve => {
    const id = ++requestId;
    pending = { id, resolve, timer: setTimeout(() => {
      killWorker();
      finishPending({ stdout: '', stderr: '', error: '运行环境没有响应，请重试。', kind: 'crash', elapsed: 0 });
    }, 10000) };
    worker.postMessage({ id, code, stdin, outputLimit: currentProblem() ? 8 * 1024 * 1024 : 65536 });
  });
}

function setSummary(state, title, message) {
  const box = elements['result-summary'];
  box.className = `result-summary ${state}`;
  box.replaceChildren();
  const symbol = document.createElement('span');
  symbol.className = 'result-symbol';
  symbol.textContent = ({ pass: '✓', fail: '!', running: '⋯', idle: '›' })[state];
  const content = document.createElement('div');
  const heading = document.createElement('strong');
  heading.textContent = title;
  const explanation = document.createElement('p');
  explanation.textContent = message;
  content.append(heading, explanation);
  box.append(symbol, content);
}

function addOutput(parent, label, text, isError = false) {
  const block = document.createElement('div');
  block.className = `output-block${isError ? ' error' : ''}`;
  const title = document.createElement('div');
  title.className = 'output-label';
  title.textContent = label;
  const pre = document.createElement('pre');
  pre.textContent = text === '' ? '（空输出）' : text.length > 16000 ? text.slice(0, 16000) + '\n… 预览已截短；判题使用完整输出。' : text;
  block.append(title, pre);
  parent.append(block);
}

function judge(result, expected, compare, stdin) {
  if (result.error?.includes('OutputLimitError')) return { state: 'fail', title: '输出超过本页上限', detail: '本次未完成答案验证。请缩小数据或下载代码本地运行。' };
  if (result.kind === 'timeout') return { state: 'fail', title: '运行超时', detail: '检查循环是否能结束、指针是否移动，以及算法复杂度。' };
  if (result.error) return { state: 'fail', title: result.kind === 'stopped' ? '已停止运行' : '运行出错', detail: result.kind === 'stopped' ? '你可以修改代码，然后重新运行。' : '查看下方错误信息，定位 main.py 中的对应行。' };
  if (!compare) return { state: 'idle', title: '运行完成', detail: '已关闭自动核对，请查看实际输出。' };
  const comparison = compareOutput(result.stdout, expected, currentProblem()?.judge || 'tokens', stdin);
  if (comparison.pass) return { state: 'pass', title: currentProblem()?.judge === 'peak' ? '答案有效' : '答案一致', detail: currentProblem()?.judge === 'peak' ? '输出的是有效峰值下标。' : '实际输出符合本题的比较规则。' };
  return { state: 'fail', title: '答案不一致', detail: comparison.message || `第 ${comparison.index + 1} 项输出：预期 ${JSON.stringify(comparison.expected) ?? '无'}，实际 ${comparison.actual === null ? '缺少输出' : JSON.stringify(comparison.actual)}。` };
}

function displayResult(parent, result, expected, compare) {
  addOutput(parent, '实际输出 · stdout', result.stdout);
  if (compare) addOutput(parent, '预期输出', expected);
  if (result.stderr) addOutput(parent, '调试输出 · stderr', result.stderr);
  if (result.error) addOutput(parent, '错误信息', result.error, true);
}

async function run(all = false, source = 'draft') {
  if (busy || !ready) return;
  const isReference = source === 'reference';
  const code = isReference ? currentReference()?.code : elements.code.value;
  if (!code?.trim()) {
    setSummary('fail', '还没有代码', '请先写入完整的 Python 程序。');
    return;
  }
  saveDraft();
  resultDraft = JSON.stringify(drafts[mode]);
  $('result-title').textContent = `${isReference ? '参考模板' : '我的尝试'} · 运行结果`;
  const cases = currentProblem()?.cases || [];
  const selectedCases = all ? cases : [{ name: '当前测试', stdin: elements.stdin.value, expected: elements.expected.value }];
  const compare = all || elements.compare.checked;
  busy = true;
  stopped = false;
  updateControls();
  runtimeStatus('Python 正在运行', 'loading');
  elements['result-details'].replaceChildren();
  elements['result-time'].textContent = '';
  setSummary('running', all ? `正在验证 ${cases.length} 组测试` : '正在运行', '每组最多运行 3 秒，你也可以随时停止。');
  elements['result-summary'].scrollIntoView({ block: 'nearest' });
  let passed = 0;
  let completed = 0;
  let elapsed = 0;
  try {
    for (const testCase of selectedCases) {
      if (stopped || !worker) break;
      const result = await execute(code, testCase.stdin);
      completed++;
      elapsed += result.elapsed || 0;
      const verdict = judge(result, testCase.expected, compare, testCase.stdin);
      if (verdict.state === 'pass') passed++;
      if (all) {
        const row = document.createElement('details');
        row.className = 'case-result';
        row.open = verdict.state === 'fail';
        const summary = document.createElement('summary');
        const badge = document.createElement('span');
        badge.className = `case-badge ${verdict.state === 'fail' ? 'fail' : ''}`;
        badge.textContent = verdict.state === 'pass' ? '通过' : verdict.title;
        const name = document.createElement('span');
        name.textContent = testCase.name;
        const time = document.createElement('span');
        time.className = 'case-time';
        time.textContent = `${(result.elapsed || 0).toFixed(1)} ms`;
        summary.append(badge, name, time);
        row.append(summary);
        addOutput(row, '本组输入', testCase.stdin);
        displayResult(row, result, testCase.expected, true);
        elements['result-details'].append(row);
      } else {
        setSummary(verdict.state, verdict.title, verdict.detail);
        displayResult(elements['result-details'], result, testCase.expected, compare);
      }
      if (result.kind) break;
    }
    if (all) {
      const interrupted = completed < selectedCases.length || stopped;
      setSummary(passed === cases.length ? 'pass' : 'fail', `${passed} / ${cases.length} 组测试通过`, interrupted ? `本次已运行 ${completed} 组，其余未运行。修改后可以再次验证。` : passed === cases.length ? isReference ? '参考模板通过本题练习用例。你的尝试代码和完成进度保持原样。' : `当前 ${cases.length} 组练习用例均通过。完成进度可在左侧手动标记。` : '展开未通过的测试，查看输入和输出差异。');
    }
    elements['result-time'].textContent = `执行 ${elapsed.toFixed(1)} ms`;
  } catch (error) {
    setSummary('fail', '运行中断', '请重新加载运行环境后重试。');
    addOutput(elements['result-details'], '错误详情', String(error), true);
    killWorker();
  } finally {
    busy = false;
    if (!worker) initializeRuntime();
    else runtimeStatus(`Python ${pythonVersion} 已就绪`);
    updateControls();
  }
}

function stop() {
  if (!busy) return;
  stopped = true;
  killWorker();
  finishPending({ stdout: '', stderr: '', error: '程序已由你停止。', kind: 'stopped', elapsed: 0 });
}

function saveDraft() {
  drafts[mode] = { code: elements.code.value, stdin: elements.stdin.value, expected: elements.expected.value, compare: elements.compare.checked };
  if (resultDraft !== null && JSON.stringify(drafts[mode]) !== resultDraft) {
    resultDraft = null;
    elements['result-details'].replaceChildren();
    elements['result-time'].textContent = '';
    setSummary('idle', '内容已修改，请重新运行', '上次结果对应的是修改前的代码或测试数据。');
  }
  try {
    localStorage.setItem(storageKey, JSON.stringify({ mode, lastProblem, drafts, completed }));
    elements['save-status'].textContent = '已保存到浏览器';
    elements['save-status'].classList.remove('save-error');
  } catch {
    elements['save-status'].textContent = '保存失败，请下载代码';
    elements['save-status'].classList.add('save-error');
  }
}

function refreshEditor() {
  const value = elements.code.value;
  $('line-numbers').textContent = Array.from({ length: value.split('\n').length }, (_, i) => i + 1).join('\n');
  $('line-numbers').scrollTop = elements.code.scrollTop;
  const before = value.slice(0, elements.code.selectionStart);
  const lines = before.split('\n');
  $('cursor-position').textContent = `第 ${lines.length} 行，第 ${lines.at(-1).length + 1} 列`;
}

function updateSampleSelection() {
  const cases = currentProblem()?.cases || [];
  document.querySelectorAll('[data-sample]').forEach(button => {
    const item = cases[Number(button.dataset.sample)];
    const active = item && elements.stdin.value.trim() === item.stdin.trim();
    button.classList.toggle('selected', Boolean(active));
    button.setAttribute('aria-pressed', String(Boolean(active)));
  });
}

function updateProgress() {
  const count = problems.filter(problem => completed[problem.id]).length;
  $('progress-count').textContent = `系列进度：${count} / ${problems.length} 题已完成`;
  $('catalog-progress').textContent = `${count} / ${problems.length} 已完成`;
  const done = Boolean(completed[mode]);
  $('toggle-complete').classList.toggle('done', done);
  $('toggle-complete').setAttribute('aria-pressed', String(done));
  $('toggle-complete').textContent = done ? '✓ 已完成 · 点击撤销' : '标记已完成';
}

function renderReference() {
  const problem = currentProblem();
  const reference = currentReference();
  $('toggle-reference').hidden = !problem;
  $('reference-panel').hidden = !problem || !showReference;
  $('code-comparison').classList.toggle('single-panel', !problem || !showReference);
  $('toggle-reference').textContent = showReference ? '收起参考' : '查看参考';
  $('toggle-reference').setAttribute('aria-expanded', String(showReference));
  $('reference-code').value = reference?.code || '';
  $('reference-code').scrollTop = 0;
  $('reference-code').scrollLeft = 0;
  $('reference-source').hidden = !reference;
  if (reference) {
    $('reference-source').href = reference.sourceUrl;
    $('reference-source').title = reference.sourceTitle;
  }
  $('reference-variant').textContent = reference ? `${problem.id} · ${reference.variant}` : referenceError || '正在加载参考代码…';
  $('reference-note').textContent = reference?.note || '完整程序包含导入、输入、算法和输出。';
  $('retry-reference').hidden = !referenceError;
  $('reference-imports-section').hidden = !reference;
  $('reference-imports').replaceChildren();
  for (const item of reference?.imports || []) {
    const row = document.createElement('li');
    const code = document.createElement('code');
    code.textContent = item.code;
    const purpose = document.createElement('span');
    purpose.textContent = item.purpose;
    row.append(code, purpose);
    $('reference-imports').append(row);
  }
  $('reference-filename').textContent = problem ? `reference_${problem.id}.py` : 'reference.py';
  $('reference-feedback').textContent = '输入输出遵循左侧本页约定。';
  $('verify-reference').textContent = `验证参考 · ${problem?.cases.length || 0} 组`;
  updateControls();
}

async function initializeReferences() {
  referenceError = '';
  $('retry-reference').disabled = true;
  renderReference();
  try { references = await loadReferences(problems); }
  catch (error) { referenceError = error.message; }
  finally {
    $('retry-reference').disabled = false;
    renderReference();
  }
}

function renderMode() {
  resultDraft = null;
  drafts[mode] ||= defaultDraft(mode);
  const draft = drafts[mode];
  const problem = currentProblem();
  elements.code.value = draft.code;
  elements.stdin.value = draft.stdin;
  elements.expected.value = draft.expected;
  elements.compare.checked = draft.compare;
  elements.expected.disabled = !draft.compare;
  $('problem-bank').hidden = !problem;
  $('problem-free').hidden = Boolean(problem);
  $('mode-bank').classList.toggle('active', Boolean(problem));
  $('mode-bank').setAttribute('aria-pressed', String(Boolean(problem)));
  $('mode-free').classList.toggle('active', !problem);
  $('mode-free').setAttribute('aria-pressed', String(!problem));
  elements['run-all'].hidden = !problem;
  $('sample-buttons').hidden = !problem;
  $('sample-buttons').replaceChildren();
  const notes = { tokens: '按空白分隔比较输出', json: '按 JSON 结构比较', unordered: '忽略结果集合的排列顺序', 'unordered-nested': '组合内外顺序均可不同', peak: '接受任意有效峰值下标' };
  $('judge-note').textContent = notes[problem?.judge || 'tokens'];
  $('resource-note').textContent = `单组限时 3 秒，输出上限 ${problem ? '8 MiB' : '64 KiB'}。内置数据是练习用例，不代表力扣完整评测。完成进度由你手动标记。`;
  if (problem) {
    $('problem-number').textContent = `LeetCode ${problem.id}`;
    $('problem-episode').textContent = `第 ${problem.episodes.join('、')} 集`;
    $('problem-title').textContent = problem.title;
    $('problem-topic').textContent = problem.topic;
    $('problem-statement').textContent = problem.statement;
    $('input-format').textContent = problem.inputFormat;
    $('output-format').textContent = problem.outputFormat;
    $('problem-source').href = problem.url;
    $('problem-position').textContent = `${problems.findIndex(p => p.id === mode) + 1} / ${problems.length}`;
    elements['run-all'].textContent = `验证本题 · ${problem.cases.length} 组`;
    problem.cases.slice(0, 6).forEach((testCase, index) => {
      const button = document.createElement('button');
      button.dataset.sample = index;
      button.textContent = `用例 ${index + 1}`;
      button.title = testCase.name;
      $('sample-buttons').append(button);
    });
  }
  elements['result-details'].replaceChildren();
  elements['result-time'].textContent = '';
  $('result-title').textContent = '我的尝试 · 运行结果';
  setSummary('idle', '准备好，就跑一遍', problem ? '在「我的尝试」编写算法，需要时可对照完整 ACM 参考。' : '可先运行求和示例，再替换为你的程序。');
  refreshEditor();
  updateSampleSelection();
  updateProgress();
  updateControls();
  renderReference();
}

function switchProblem(id) {
  if (busy || mode === id) return;
  saveDraft();
  mode = id;
  if (id !== 'free') lastProblem = id;
  renderMode();
  saveDraft();
}

function renderCatalog() {
  const filtered = filterProblems(problems, $('problem-search').value, $('topic-filter').value, $('todo-filter').checked, completed);
  $('catalog-result-count').textContent = `找到 ${filtered.length} 道题`;
  const list = $('catalog-list');
  list.replaceChildren();
  let previousEpisode;
  let section;
  for (const problem of filtered) {
    if (problem.episode !== previousEpisode) {
      previousEpisode = problem.episode;
      section = document.createElement('section');
      section.className = 'catalog-group';
      const heading = document.createElement('h3');
      heading.textContent = `第 ${String(problem.episode).padStart(2, '0')} 集 · ${problem.topic}`;
      section.append(heading);
      list.append(section);
    }
    const row = document.createElement('button');
    row.className = `catalog-row${problem.id === mode ? ' selected' : ''}`;
    row.dataset.problem = problem.id;
    row.setAttribute('aria-label', `${problem.id} ${problem.title}${completed[problem.id] ? '，已完成' : ''}`);
    for (const [className, content] of [['catalog-id', problem.id], ['catalog-name', problem.title], ['catalog-case-count', `${problem.cases.length} 组测试`], ['catalog-done', completed[problem.id] ? '✓' : '']]) {
      const span = document.createElement('span');
      span.className = className;
      span.textContent = content;
      row.append(span);
    }
    row.addEventListener('click', () => { $('catalog-dialog').close(); switchProblem(problem.id); });
    section.append(row);
  }
  if (!filtered.length) {
    const empty = document.createElement('p');
    empty.className = 'catalog-empty';
    empty.textContent = '没有匹配的题目，试试题号、关键词，或调整分类。';
    list.append(empty);
  }
  updateProgress();
}

$('catalog-count').textContent = `${problems.length} 题`;
for (const topic of [...new Set(problems.map(p => p.topic))]) {
  const option = document.createElement('option');
  option.value = topic;
  option.textContent = topic;
  $('topic-filter').append(option);
}
$('mode-bank').addEventListener('click', () => switchProblem(lastProblem));
$('mode-free').addEventListener('click', () => switchProblem('free'));
$('open-catalog').addEventListener('click', () => { renderCatalog(); $('catalog-dialog').showModal(); $('problem-search').focus(); });
$('close-catalog').addEventListener('click', () => $('catalog-dialog').close());
$('catalog-dialog').addEventListener('click', event => { if (event.target === $('catalog-dialog')) $('catalog-dialog').close(); });
for (const id of ['problem-search', 'topic-filter', 'todo-filter']) $(id).addEventListener('input', renderCatalog);
$('previous-problem').addEventListener('click', () => { const index = problems.findIndex(p => p.id === mode); if (index > 0) switchProblem(problems[index - 1].id); });
$('next-problem').addEventListener('click', () => { const index = problems.findIndex(p => p.id === mode); if (index < problems.length - 1) switchProblem(problems[index + 1].id); });
$('toggle-complete').addEventListener('click', () => { if (busy || mode === 'free') return; if (completed[mode]) delete completed[mode]; else completed[mode] = true; saveDraft(); updateProgress(); });

elements.code.addEventListener('input', () => { refreshEditor(); saveDraft(); });
elements.code.addEventListener('scroll', () => { $('line-numbers').scrollTop = elements.code.scrollTop; });
elements.code.addEventListener('click', refreshEditor);
elements.code.addEventListener('keyup', refreshEditor);
elements.code.addEventListener('keydown', event => {
  if (busy) return;
  if (event.key === 'Tab') {
    event.preventDefault();
    const start = elements.code.selectionStart;
    const end = elements.code.selectionEnd;
    if (start !== end) {
      const lineStart = elements.code.value.lastIndexOf('\n', start - 1) + 1;
      const selected = elements.code.value.slice(lineStart, end);
      const changed = selected.split('\n').map(line => event.shiftKey ? line.replace(/^ {1,4}/, '') : `    ${line}`).join('\n');
      elements.code.setRangeText(changed, lineStart, end, 'select');
    } else if (event.shiftKey) {
      const before = elements.code.value.slice(0, start);
      const count = Math.min(4, before.match(/ *$/)[0].length);
      elements.code.setRangeText('', start - count, start, 'end');
    } else {
      elements.code.setRangeText('    ', start, end, 'end');
    }
    refreshEditor();
    saveDraft();
  } else if (event.key === 'Enter' && !event.metaKey && !event.ctrlKey && !event.isComposing) {
    event.preventDefault();
    const before = elements.code.value.slice(0, elements.code.selectionStart);
    const line = before.split('\n').at(-1);
    const indent = line.match(/^\s*/)[0] + (line.trimEnd().endsWith(':') ? '    ' : '');
    elements.code.setRangeText(`\n${indent}`, elements.code.selectionStart, elements.code.selectionEnd, 'end');
    refreshEditor();
    saveDraft();
  }
});

for (const key of ['stdin', 'expected']) elements[key].addEventListener('input', () => { saveDraft(); updateSampleSelection(); });
elements.compare.addEventListener('change', () => { elements.expected.disabled = !elements.compare.checked; saveDraft(); });
$('sample-buttons').addEventListener('click', event => {
  const button = event.target.closest('[data-sample]');
  if (!button || busy) return;
  const sample = currentProblem().cases[Number(button.dataset.sample)];
  elements.stdin.value = sample.stdin;
  elements.expected.value = sample.expected;
  elements.compare.checked = true;
  elements.expected.disabled = false;
  saveDraft();
  updateSampleSelection();
});
$('template').addEventListener('click', () => {
  if (elements.code.value !== currentTemplate() && !confirm('恢复输入输出模板会替换当前代码。需要保留时，请先下载代码。是否继续？')) return;
  elements.code.value = currentTemplate();
  saveDraft();
  refreshEditor();
});
$('focus-solution').addEventListener('click', () => {
  const match = elements.code.value.match(/^.*(?:# TODO|# 在这里|raise NotImplementedError|def solve\().*$/m);
  const position = match?.index || 0;
  elements.code.focus();
  elements.code.setSelectionRange(position, position);
  elements.code.scrollTop = Math.max(0, elements.code.value.slice(0, position).split('\n').length - 4) * 25;
  refreshEditor();
});
$('download').addEventListener('click', () => {
  downloadCode(elements.code.value, 'main.py');
});
function downloadCode(code, filename) {
  const url = URL.createObjectURL(new Blob([code], { type: 'text/x-python;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('toggle-reference').addEventListener('click', () => {
  showReference = !showReference;
  try { localStorage.setItem('acm-reference-visible', String(showReference)); } catch {}
  renderReference();
});
$('retry-reference').addEventListener('click', initializeReferences);
$('copy-reference').addEventListener('click', async () => {
  const reference = currentReference();
  if (!reference) return;
  try {
    await navigator.clipboard.writeText(reference.code);
    $('reference-feedback').textContent = '参考代码已复制，可粘贴到你选择的位置。';
  } catch {
    $('reference-code').focus();
    $('reference-code').select();
    $('reference-feedback').textContent = '请按 Ctrl/Cmd + C 复制已选中的参考代码。';
  }
});
$('download-reference').addEventListener('click', () => {
  if (currentReference()) downloadCode(currentReference().code, `reference_${mode}.py`);
});
$('run-reference').addEventListener('click', () => run(false, 'reference'));
$('verify-reference').addEventListener('click', () => run(true, 'reference'));
elements.run.addEventListener('click', () => run());
elements['run-all'].addEventListener('click', () => run(true));
elements.stop.addEventListener('click', stop);
elements.retry.addEventListener('click', initializeRuntime);
document.addEventListener('keydown', event => {
  if ((event.metaKey || event.ctrlKey) && event.key === 'Enter') { event.preventDefault(); run(); }
});
if (!/Mac|iPhone|iPad/.test(navigator.platform)) $('shortcut').textContent = 'Ctrl Enter';

renderMode();
initializeRuntime();
initializeReferences();

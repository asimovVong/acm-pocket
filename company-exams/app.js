import { shelfSteps, balancedCuts, segmentSums } from './models.mjs';
const $ = id => document.getElementById(id);
const key = 'company-exams-v1';
let catalog;
try {
  const response = await fetch('./catalog.json');
  if (!response.ok) throw new Error(`题库请求失败 (${response.status})`);
  catalog = await response.json();
} catch (error) {
  $('load-error').hidden = false;
  $('load-error').textContent = `无法读取题库。请通过本地网站地址打开本页，然后刷新。${error.message}`;
  throw error;
}
let saved = { drafts: {}, completed: [] };
try {
  const value = JSON.parse(localStorage.getItem(key));
  if (value && typeof value.drafts === 'object' && value.drafts && Array.isArray(value.completed)) saved = value;
} catch { /* Storage may be unavailable; editing remains usable. */ }
let current, activeTab = 'learn', demoStep = 0, cuts = [1, 2, 3];
let worker = null, ready = false, busy = false, pending = null, bootTimer, serial = 0;
const buttons = ['run', 'run-all', 'run-reference', 'verify-reference'];
function persist() {
  try {
    localStorage.setItem(key, JSON.stringify(saved));
    $('save-status').textContent = '已保存到当前浏览器';
  } catch {
    $('save-status').textContent = '保存失败，请下载我的代码';
  }
}
function saveDraft() {
  if (!current) return;
  saved.drafts[current.id] = { code: $('code').value, stdin: $('stdin').value, expected: $('expected').value };
  persist();
}
function renderNavigation() {
  const query = $('search').value.trim().toLowerCase();
  const filtered = catalog.filter(p => `${p.company} ${p.date} ${p.title} ${p.topic}`.toLowerCase().includes(query));
  $('problem-list').replaceChildren(...filtered.map(p => {
    const a = document.createElement('a');
    a.className = 'problem-link'; a.href = `#${p.id}`;
    if (p.id === current?.id) a.setAttribute('aria-current', 'page');
    a.innerHTML = `<span class="number">${p.number}</span><strong>${p.title}</strong><span class="done-dot">${saved.completed.includes(p.id) ? '✓' : ''}</span>`;
    return a;
  }));
  $('empty-search').hidden = filtered.length > 0;
  const count = catalog.filter(p => saved.completed.includes(p.id)).length;
  $('progress').textContent = `${count} / ${catalog.length}`;
  $('progress-bar').value = count;
}
function setResult(title, text, status = '') {
  $('result-title').textContent = title;
  $('result').textContent = text;
  $('result').className = status;
}
function refreshControls() {
  for (const id of buttons) $(id).disabled = !ready || busy;
  for (const id of ['code', 'stdin', 'expected']) $(id).readOnly = busy;
  $('sample').disabled = busy;
  $('stop').hidden = !busy;
}
function selectProblem() {
  const next = catalog.find(p => `#${p.id}` === location.hash) || current || catalog[0];
  if (current?.id === next.id) return;
  if (busy) stopRun('已切换题目，上一次运行已取消。');
  saveDraft();
  current = next;
  demoStep = 0; cuts = [1, 2, 3];
  document.title = `${current.title} · 滴滴笔试手册`;
  for (const prop of ['title', 'summary', 'topic', 'insight']) $(prop).textContent = current[prop];
  $('complexity').textContent = current.complexity;
  $('problem-kicker').textContent = `第 ${current.number} 题 / 共 2 题`;
  $('lesson').innerHTML = current.lesson;
  $('toc').replaceChildren();
  $('reading-shortcuts').replaceChildren();
  $('lesson').querySelectorAll('h2').forEach((heading, index) => {
    heading.id = `section-${index}`;
    const a = document.createElement('a');
    a.href = `#${current.id}`; a.textContent = heading.textContent;
    a.addEventListener('click', event => { event.preventDefault(); heading.scrollIntoView({ behavior: 'auto', block: 'start' }); });
    $('toc').append(a);
    if (index < 6) {
      const shortcut = document.createElement('a');
      shortcut.href = `#${current.id}`;
      shortcut.textContent = index === 5 ? '解题推导' : heading.textContent;
      shortcut.addEventListener('click', event => { event.preventDefault(); heading.scrollIntoView({ behavior: 'auto', block: 'start' }); });
      $('reading-shortcuts').append(shortcut);
    }
  });
  $('source').href = current.source;
  $('download-original').href = `${current.directory}/原题.md`;
  $('download-note').href = `${current.directory}/讲解.md`;
  $('download-source').href = `${current.directory}/solution.py`;
  $('reference-download').href = `${current.directory}/solution.py`;
  $('reference').value = current.reference;
  $('reference-details').open = false;
  $('copy-status').textContent = '';
  const draft = saved.drafts[current.id];
  $('code').value = typeof draft?.code === 'string' ? draft.code : current.starter;
  $('stdin').value = typeof draft?.stdin === 'string' ? draft.stdin : current.cases[0].stdin;
  $('expected').value = typeof draft?.expected === 'string' ? draft.expected : current.cases[0].expected;
  $('sample').replaceChildren(...current.cases.map((c, index) => new Option(`${c.source === 'article' ? '原文' : '补充'} · ${c.name.replace('原文', '')}`, String(index))));
  const custom = new Option('当前草稿 / 自定义输入', 'custom');
  $('sample').add(custom); $('sample').value = draft ? 'custom' : '0';
  $('complete').setAttribute('aria-pressed', String(saved.completed.includes(current.id)));
  $('complete').textContent = saved.completed.includes(current.id) ? '✓ 已完成 · 点击撤销' : '标记已完成';
  $('next-problem').textContent = current === catalog[0] ? '下一题：管材四切' : '回看：层板限差';
  setResult('运行结果', '运行后在这里查看输出。');
  $('problem-content').hidden = false;
  renderNavigation(); renderDemo(); showTab(activeTab); persist();
}
function showTab(name) {
  activeTab = name;
  for (const tab of ['learn', 'demo', 'practice']) {
    $(`${tab}-panel`).hidden = tab !== name;
    $(`tab-${tab}`).setAttribute('aria-selected', String(tab === name));
    $(`tab-${tab}`).tabIndex = tab === name ? 0 : -1;
  }
  if (name === 'practice' && !worker) initializeRuntime();
}
function renderDemo() {
  if (current.demo === 'shelf') {
    $('demo-description').textContent = '原文样例：高度 [1, 2, 3]，d = 1。按从小到大的顺序，计算每个箱子的插入位置数。';
    const steps = shelfSteps([1,2,3], 1), s = steps[demoStep];
    $('demo').innerHTML = `<div class="demo-board"><div class="demo-caption">排序后的高度。蓝色是当前箱子，绿色是可接在其后的位置对应的已有箱子。</div><div class="demo-boxes">${s.a.map((x,i)=>`<div class="shelf-box ${i===s.i?'active':i>s.i&&i<s.right?'eligible':''}" style="height:${60+x*26}px"><strong>${x}</strong><small>下标 ${i}</small></div>`).join('')}</div><div class="demo-formula">right − i = ${s.right} − ${s.i} = ${s.choices} 个位置</div><p class="demo-description">当前高度是 ${s.value}，已有箱子中不超过 ${s.value + 1} 的有 ${s.choices - 1} 个；再加上放在排列开头的 1 个位置。累计答案：${steps.slice(0, demoStep + 1).map(x=>x.choices).join(' × ')} = <strong>${s.answer}</strong>。</p><div class="demo-buttons"><span>第 ${demoStep+1} / 3 步</span><button id="demo-prev" ${demoStep===0?'disabled':''}>上一步</button><button id="demo-next" ${demoStep===2?'disabled':''}>下一步</button><button id="demo-reset">重新看</button></div><table class="demo-table"><thead><tr><th>i</th><th>高度</th><th>right</th><th>位置数</th><th>累计</th></tr></thead><tbody>${steps.map((x,i)=>`<tr class="${i===demoStep?'active':''}"><td>${x.i}</td><td>${x.value}</td><td>${x.right}</td><td>${x.choices}</td><td>${i<=demoStep?x.answer:'—'}</td></tr>`).join('')}</tbody></table></div>`;
    $('demo-prev').onclick = () => { demoStep--; renderDemo(); };
    $('demo-next').onclick = () => { demoStep++; renderDemo(); };
    $('demo-reset').onclick = () => { demoStep=0; renderDemo(); };
  } else {
    $('demo-description').textContent = '原文样例：[4, 5, 1, 2, 8]。先拖动中间切口，再用按钮让左右各自尽量均分。';
    $('demo').innerHTML = `<div class="demo-board"><div class="demo-caption">从左到右是四段，颜色只用于区分区间。切口数字表示前面有几个元素。</div><div id="pipe-visual" class="pipe-visual"></div><div id="pipe-range" class="demo-formula" aria-live="polite"></div><div class="cut-controls"><label>左切口 <output id="left-value"></output><input id="cut-left" type="range" min="1" aria-label="左切口"></label><label>中间切口 <output id="middle-value"></output><input id="cut-middle" type="range" min="2" max="3" aria-label="中间切口"></label><label>右切口 <output id="right-value"></output><input id="cut-right" type="range" max="4" aria-label="右切口"></label></div><div class="demo-buttons"><button class="primary" id="balance">让左右各自尽量平衡</button><button id="pipe-reset">恢复初始切法</button></div><p id="pipe-explanation" class="demo-description" style="margin:22px 0 0"></p></div>`;
    for(const [id, i] of [['cut-left',0],['cut-middle',1],['cut-right',2]]) $(id).oninput = () => {
      cuts[i] = Number($(id).value);
      cuts[0] = Math.min(cuts[0], cuts[1]-1);
      cuts[2] = Math.max(cuts[2], cuts[1]+1);
      renderPipe();
    };
    $('balance').onclick = () => { cuts=balancedCuts([4,5,1,2,8], cuts[1]); renderPipe(); };
    $('pipe-reset').onclick = () => { cuts=[1,2,3]; renderPipe(); };
    renderPipe();
  }
}
function renderPipe() {
  const a = [4,5,1,2,8], sums = segmentSums(a, cuts), edges=[0,...cuts,5];
  const colors=['#355ba0','#287762','#9a6328','#7c4b95'];
  $('pipe-visual').innerHTML=sums.map((sum,i)=>`<div class="pipe-segment" style="--segment:${colors[i]}"><div class="pipe-values">${a.slice(edges[i],edges[i+1]).join(' , ')}</div><small>第 ${i+1} 段的和</small><strong>${sum}</strong></div>`).join('');
  const gap = Math.max(...sums)-Math.min(...sums);
  $('pipe-range').textContent=`最大 ${Math.max(...sums)} − 最小 ${Math.min(...sums)} = ${gap}`;
  $('cut-left').max=cuts[1]-1; $('cut-right').min=cuts[1]+1;
  for(const [i,name] of ['left','middle','right'].entries()) { $(`cut-${name}`).value=cuts[i]; $(`${name}-value`).textContent=cuts[i]; }
  const best=segmentSums(a,balancedCuts(a,cuts[1]));
  const local=Math.max(...best)-Math.min(...best);
  $('pipe-explanation').textContent=`中间切在第 ${cuts[1]} 个数后。这一刀固定时，最小极差是 ${local}；当前是 ${gap}。${gap===local?'当前已是这个中间切口下的最优切法。':'试着点击“让左右各自尽量平衡”，看看段和怎样改变。'}两个中间切口都比较后，全局答案是 5。`;
}
function terminateWorker() {
  worker?.terminate(); worker=null; ready=false; clearTimeout(bootTimer);
}
function resolvePending(result) {
  if (!pending) return;
  const p=pending; pending=null; clearTimeout(p.timer); p.resolve(result);
}
function runtimeFailure(message) {
  terminateWorker();
  $('runtime-status').textContent='Python 加载失败'; $('retry').hidden=false;
  resolvePending({ error:message, stdout:'' });
  setResult('运行环境未就绪', `${message}\n请重新加载，或下载代码在本机运行。当前草稿仍保留。`, 'fail');
  refreshControls();
}
function initializeRuntime() {
  terminateWorker(); $('retry').hidden=true;
  $('runtime-status').textContent='正在加载 Python…'; refreshControls();
  let w;
  try { w=new Worker('../worker.js', {type:'module'}); worker=w; }
  catch (error) { runtimeFailure(String(error)); return; }
  bootTimer=setTimeout(()=> { if(worker===w) runtimeFailure('首次加载超过 90 秒，请检查网络。'); }, 90000);
  w.onmessage=({data})=> {
    if(worker!==w) return;
    if(data.type==='ready') {
      clearTimeout(bootTimer); ready=true;
      $('runtime-status').textContent=`Python ${data.version} 已就绪`; refreshControls();
    } else if(data.type==='init-error') runtimeFailure(data.error);
    else if(pending && data.id===pending.id) {
      if(data.type==='started') {
        clearTimeout(pending.timer);
        pending.timer=setTimeout(()=> {
          terminateWorker(); $('runtime-status').textContent='运行已超时'; $('retry').hidden=false;
          resolvePending({error:'单组运行超过 3 秒，请检查死循环或降低复杂度。',stdout:''});
        },3000);
      } else if(data.type==='result') resolvePending(data);
    }
  };
  w.onerror=event=> { event.preventDefault(); if(worker===w) runtimeFailure(event.message || '运行环境意外退出'); };
}
function execute(code,stdin) {
  return new Promise(resolve=> {
    const id=++serial;
    pending={id,resolve,timer:setTimeout(()=> {
      terminateWorker(); $('runtime-status').textContent='运行环境无响应'; $('retry').hidden=false;
      resolvePending({error:'运行环境无响应，请重新加载。',stdout:''});
    },10000)};
    worker.postMessage({id,code,stdin,outputLimit:65536});
  });
}
let runGeneration=0;
async function run(source, all) {
  if(!ready || busy) return;
  const generation=++runGeneration;
  busy=true; saveDraft(); refreshControls();
  const title = source==='reference'?'参考代码':'我的尝试';
  const code = source==='reference'?current.reference:$('code').value;
  const cases=all?current.cases:[{name:'当前输入',stdin:$('stdin').value,expected:$('expected').value}];
  setResult(`${title} · ${all?'验证全部用例':'运行结果'}`, '正在运行…');
  const lines=[]; let passed=0;
  try {
    for(const c of cases) {
      const r=await execute(code,c.stdin);
      if(generation!==runGeneration) return;
      const normalize=s=>String(s??'').trim().split(/\s+/).filter(Boolean).join(' ');
      const ok=!r.error && normalize(r.stdout)===normalize(c.expected);
      if(ok) passed++;
      lines.push(`${ok?'✓':'✗'} ${c.name}${r.elapsed!=null?` (${r.elapsed.toFixed(1)} ms)`:''}`);
      if(!all || !ok) lines.push(`预期：${c.expected.trim() || '(空输出)'}\n实际：${r.stdout?.trim() || '(空输出)'}`);
      if(r.stderr) lines.push(`标准错误：${r.stderr}`);
      if(r.error) {lines.push(r.error); break;}
    }
    setResult(`${title} · ${passed} / ${cases.length} 通过`, lines.join('\n\n'), passed===cases.length?'pass':'fail');
  } catch(error) {
    if(generation===runGeneration) setResult(`${title} · 运行失败`,String(error),'fail');
  } finally {
    if(generation===runGeneration) {busy=false;refreshControls();}
  }
}
function stopRun(message='已停止运行。草稿已保留，点击“重新加载”恢复运行环境。') {
  runGeneration++; terminateWorker(); resolvePending({error:'已取消',stdout:''}); busy=false;
  $('runtime-status').textContent='Python 已停止'; $('retry').hidden=false; refreshControls();
  setResult('运行已停止',message);
}
function download(text,filename) {
  const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));
  const a=document.createElement('a'); a.href=url; a.download=filename; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
for(const name of ['learn','demo','practice']) $(`tab-${name}`).onclick=()=>showTab(name);
const tabNames=['learn','demo','practice'];
document.querySelector('.tabs').onkeydown=event=> {
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
  event.preventDefault(); let i=tabNames.indexOf(activeTab);
  i=event.key==='Home'?0:event.key==='End'?2:(i+(event.key==='ArrowRight'?1:2))%3;
  showTab(tabNames[i]); $(`tab-${tabNames[i]}`).focus();
};
$('search').oninput=renderNavigation;
$('complete').onclick=()=> {
  saved.completed=saved.completed.includes(current.id)?saved.completed.filter(id=>id!==current.id):[...saved.completed,current.id];
  $('complete').setAttribute('aria-pressed',String(saved.completed.includes(current.id)));
  $('complete').textContent=saved.completed.includes(current.id)?'✓ 已完成 · 点击撤销':'标记已完成';
  persist();renderNavigation();
};
$('next-problem').onclick=()=> {location.hash=catalog[(catalog.indexOf(current)+1)%catalog.length].id; $('content').scrollIntoView();};
$('sample').onchange=()=> {
  const c=current.cases[Number($('sample').value)]; if(!c) return;
  $('stdin').value=c.stdin; $('expected').value=c.expected; saveDraft();
  setResult('输入已更新','请重新运行，之前的结果不再对应当前输入。');
};
for(const id of ['code','stdin','expected']) $(id).oninput=()=> {
  if(id!=='code') $('sample').value='custom';
  saveDraft(); setResult('内容已修改','请重新运行，以核对当前代码和输入。');
};
$('code').onkeydown=event=> {
  if(busy) return;
  if(event.key==='Tab') {
    event.preventDefault(); const el=event.target, start=el.selectionStart, end=el.selectionEnd;
    el.setRangeText('    ',start,end,'end'); el.dispatchEvent(new Event('input'));
  } else if(event.key==='Enter' && (event.metaKey || event.ctrlKey)) {event.preventDefault();run('draft',false);}
  else if(event.key==='Enter') {
    event.preventDefault(); const el=event.target,start=el.selectionStart;
    const before=el.value.slice(0,start).split('\n').at(-1);
    const indent=before.match(/^\s*/)[0]+(before.trimEnd().endsWith(':')?'    ':'');
    el.setRangeText('\n'+indent,start,el.selectionEnd,'end'); el.dispatchEvent(new Event('input'));
  }
};
$('download-draft').onclick=()=>download($('code').value,`${current.title}-我的尝试.py`);
$('copy-reference').onclick=async()=> {
  try {await navigator.clipboard.writeText(current.reference);$('copy-status').textContent='参考已复制，练习草稿保持不变。';}
  catch {$('copy-status').textContent='浏览器未允许复制，请选择参考代码手动复制，或下载参考文件。';}
};
$('run').onclick=()=>run('draft',false); $('run-all').onclick=()=>run('draft',true);
$('run-reference').onclick=()=>run('reference',false); $('verify-reference').onclick=()=>run('reference',true);
$('stop').onclick=()=>stopRun(); $('retry').onclick=initializeRuntime;
window.addEventListener('hashchange',selectProblem);
window.addEventListener('pagehide',saveDraft);
selectProblem();

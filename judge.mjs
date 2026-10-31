const canonical = value => JSON.stringify(value);

function compareJSON(actual, expected, rule) {
  let a, b;
  try { a = JSON.parse(actual); b = JSON.parse(expected); }
  catch { return { pass: false, message: '输出应为合法 JSON。列表或字符串集合请使用 print(json.dumps(answer, ensure_ascii=False))。' }; }
  if (rule === 'unordered' || rule === 'unordered-nested') {
    if (!Array.isArray(a) || !Array.isArray(b)) return { pass: false, message: '本题需要输出 JSON 数组。' };
    if (rule === 'unordered-nested') {
      if (![...a, ...b].every(Array.isArray)) return { pass: false, message: '本题需要输出二维 JSON 数组，每个组合放在一个子数组中。' };
      a = a.map(row => row.map(canonical).sort());
      b = b.map(row => row.map(canonical).sort());
    }
    a = a.map(canonical).sort();
    b = b.map(canonical).sort();
  }
  const pass = canonical(a) === canonical(b);
  return pass ? { pass: true } : { pass: false, message: '输出内容或结构与预期不一致；已按本题规则处理结果顺序。' };
}

function comparePeak(actual, stdin) {
  const tokens = stdin.trim().split(/\s+/);
  const values = tokens.map(Number);
  const [n, ...nums] = values;
  if (!Number.isInteger(n) || n < 1 || nums.length !== n || !values.every(Number.isFinite)) return { pass: false, message: '本题输入第一行是 n，第二行是 n 个数组元素。请检查输入。' };
  if (!/^[-+]?\d+$/.test(actual.trim())) return { pass: false, message: '请只输出一个峰值下标（从 0 开始）。' };
  const index = Number(actual.trim());
  const pass = Number.isInteger(index) && index >= 0 && index < n && (index === 0 || nums[index] > nums[index - 1]) && (index === n - 1 || nums[index] > nums[index + 1]);
  return pass ? { pass: true } : { pass: false, message: '输出的下标不是峰值：对应元素必须严格大于左右相邻元素（边界只比较一侧）。' };
}

export function compareOutput(actual, expected, rule = 'tokens', stdin = '') {
  if (rule === 'peak') return comparePeak(actual, stdin);
  if (rule !== 'tokens') return compareJSON(actual, expected, rule);
  const tokens = value => value.match(/\S+/gu) || [];
  const actualTokens = tokens(actual);
  const expectedTokens = tokens(expected);
  for (let index = 0; index < Math.max(actualTokens.length, expectedTokens.length); index++) {
    if (actualTokens[index] !== expectedTokens[index]) {
      return { pass: false, index, actual: actualTokens[index] ?? null, expected: expectedTokens[index] ?? null };
    }
  }
  return { pass: true };
}

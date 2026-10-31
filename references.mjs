export async function loadReferences(problems) {
  const groups = await Promise.all(['arrays', 'structures', 'dp'].map(async group => {
    const response = await fetch(`./data/references-${group}.json`);
    if (!response.ok) throw new Error(`参考代码加载失败（${response.status}），可继续编写自己的代码。`);
    return response.json();
  }));
  const entries = groups.flat();
  const references = new Map(entries.map(entry => [entry.id, entry]));
  if (references.size !== entries.length || references.size !== problems.length || problems.some(problem => !references.get(problem.id)?.code)) {
    throw new Error('参考代码不完整，请重试加载。');
  }
  return references;
}

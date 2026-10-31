export async function loadCatalog() {
  const paths = ['arrays', 'structures', 'dp'];
  const groups = await Promise.all(paths.map(async name => {
    const response = await fetch(`./data/${name}.json`);
    if (!response.ok) throw new Error(`题库 ${name} 加载失败（${response.status}）`);
    return response.json();
  }));
  const manifestResponse = await fetch('./data/source-manifest.json');
  if (!manifestResponse.ok) throw new Error('题目目录加载失败');
  const manifest = await manifestResponse.json();
  const order = [...new Set(manifest.map(item => item.id))];
  const byId = new Map(groups.flat().map(item => [item.id, item]));
  if (byId.size !== order.length || order.some(id => !byId.has(id))) throw new Error('题库数据不完整，请刷新页面。');
  return order.map(id => byId.get(id));
}

export function filterProblems(problems, query = '', topic = '', onlyTodo = false, completed = {}) {
  const needle = query.trim().toLowerCase();
  return problems.filter(problem => (!topic || problem.topic === topic) && (!onlyTodo || !completed[problem.id]) && (!needle || `${problem.id} ${problem.title} ${problem.topic} 第${problem.episode}集`.toLowerCase().includes(needle)));
}

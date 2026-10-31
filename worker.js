let execute;

async function initialize() {
  try {
    const base = 'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/';
    const [{ loadPyodide }, response] = await Promise.all([
      import(`${base}pyodide.mjs`),
      fetch('./runner.py'),
    ]);
    if (!response.ok) throw new Error('无法读取 Python 运行文件');
    const python = await loadPyodide({ indexURL: base });
    await python.runPythonAsync(await response.text());
    execute = python.globals.get('execute_code_json');
    postMessage({ type: 'ready', version: python.runPython('sys.version.split()[0]') });
  } catch (error) {
    postMessage({ type: 'init-error', error: String(error) });
  }
}

self.onmessage = event => {
  const { id, code, stdin, outputLimit = 65536 } = event.data;
  if (!execute) return;
  postMessage({ type: 'started', id });
  const start = performance.now();
  try {
    const result = JSON.parse(execute(code, stdin, outputLimit));
    postMessage({ type: 'result', id, ...result, elapsed: performance.now() - start });
  } catch (error) {
    postMessage({ type: 'result', id, stdout: '', stderr: '', error: String(error), elapsed: performance.now() - start });
  }
};

initialize();

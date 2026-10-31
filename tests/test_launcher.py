import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'launcher.py'


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), '缺少一键启动程序 launcher.py')
        spec = importlib.util.spec_from_file_location('acm_launcher', SCRIPT)
        self.launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.launcher)
        self.temp = tempfile.TemporaryDirectory(prefix='acm-launch-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / '带空格的 ACM 包'
        self.root.mkdir()
        (self.root / 'index.html').write_text('<title>ACM 练习台 · Python</title>', encoding='utf-8')
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def stop_child(self, process):
        process.terminate()
        process.wait()

    def test_start_from_path_with_spaces_and_reuse_existing_server(self):
        url, pid = self.launcher.ensure_server(self.root, self.port)
        self.assertIsNotNone(pid)
        self.addCleanup(self.stop_child, pid)
        with self.opener.open(url, timeout=3) as response:
            self.assertIn('ACM 练习台', response.read().decode())
        same_url, second_pid = self.launcher.ensure_server(self.root, self.port)
        self.assertEqual(same_url, url)
        self.assertIsNone(second_pid, '重复启动不应创建第二个服务')

    def test_unrelated_service_is_not_reused_or_terminated(self):
        (self.root / 'index.html').write_text('another application')
        proc = subprocess.Popen([sys.executable, '-m', 'http.server', str(self.port), '--bind', '127.0.0.1', '--directory', str(self.root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(proc.wait)
        self.addCleanup(proc.terminate)
        for _ in range(40):
            try:
                with self.opener.open(f'http://127.0.0.1:{self.port}/', timeout=1):
                    break
            except OSError:
                time.sleep(.05)
        with self.assertRaisesRegex(RuntimeError, '占用'):
            self.launcher.ensure_server(self.root, self.port)
        self.assertIsNone(proc.poll())

    def test_concurrent_launchers_leave_one_server_running_after_they_exit(self):
        code = (
            'import json, sys; from pathlib import Path; '
            'from launcher import ensure_server; '
            'url, proc = ensure_server(Path(sys.argv[1]), int(sys.argv[2])); '
            'print(json.dumps([url, proc.pid if proc else None]))'
        )
        children = [subprocess.Popen(
            [sys.executable, '-X', 'utf8', '-c', code, str(self.root), str(self.port)],
            cwd=SCRIPT.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8',
        ) for _ in range(2)]
        records = []
        for child in children:
            output, error = child.communicate(timeout=30)
            self.assertEqual(child.returncode, 0, error)
            record = json.loads(output)
            records.append(record)
            if record[1]:
                self.addCleanup(os.kill, record[1], signal.SIGTERM)
        self.assertEqual(sum(pid is not None for _, pid in records), 1)
        with self.opener.open(records[0][0], timeout=3) as response:
            self.assertIn('ACM 练习台', response.read().decode())

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS shell integration')
    def test_install_is_idempotent_and_preserves_existing_command(self):
        home = Path(self.temp.name) / 'home'
        home.mkdir()
        self.launcher.install_command(home)
        self.launcher.install_command(home)
        target = home / '.local/bin/acm'
        self.assertEqual(target.resolve(), SCRIPT)
        result = subprocess.run(['/bin/zsh', '-c', '. "$HOME/.zshrc"; command -v acm'], env={'HOME': str(home), 'PATH': '/usr/bin:/bin'}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(target))
        target.unlink()
        target.write_text('existing user command')
        with self.assertRaises(RuntimeError):
            self.launcher.install_command(home)
        self.assertEqual(target.read_text(), 'existing user command')

    @unittest.skipUnless(sys.platform == 'darwin', 'macOS shell integration')
    def test_install_preserves_existing_bash_login_configuration(self):
        home = Path(self.temp.name) / 'bash-home'
        home.mkdir()
        (home / '.profile').write_text('export ACM_TEST_SENTINEL=preserved\n')
        self.launcher.install_command(home)
        result = subprocess.run(['/bin/bash', '--login', '-c', 'printf "%s\\n" "$ACM_TEST_SENTINEL"; command -v acm'], env={'HOME': str(home), 'PATH': '/usr/bin:/bin'}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ['preserved', str(home / '.local/bin/acm')])


if __name__ == '__main__':
    unittest.main()

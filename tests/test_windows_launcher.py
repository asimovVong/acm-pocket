"""Real cmd.exe / HKCU integration tests, run by the Windows CI job."""
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'requires Windows')
class WindowsLauncherTests(unittest.TestCase):
    def setUp(self):
        import winreg
        self.winreg = winreg
        self.temp = tempfile.TemporaryDirectory(prefix='acm-win-test-')
        self.addCleanup(self.temp.cleanup)
        self.package = Path(self.temp.name) / '中文 & 空格 ACM'
        self.package.mkdir()
        for name in ('launcher.py', '启动ACM.cmd', '安装快捷命令.cmd'):
            shutil.copy2(ROOT / name, self.package / name)
        spec = importlib.util.spec_from_file_location('win_launcher', self.package / 'launcher.py')
        self.launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.launcher)
        self.bin_dir = Path(self.temp.name) / '快捷 命令'
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
            try:
                self.original_path = winreg.QueryValueEx(key, 'Path')
            except FileNotFoundError:
                self.original_path = None
        self.addCleanup(self.restore_user_path)

    def restore_user_path(self):
        reg = self.winreg
        with reg.CreateKey(reg.HKEY_CURRENT_USER, 'Environment') as key:
            if self.original_path is None:
                try:
                    reg.DeleteValue(key, 'Path')
                except FileNotFoundError:
                    pass
            else:
                value, kind = self.original_path
                reg.SetValueEx(key, 'Path', 0, kind, value)

    def read_user_path(self):
        with self.winreg.OpenKey(self.winreg.HKEY_CURRENT_USER, 'Environment') as key:
            return self.winreg.QueryValueEx(key, 'Path')

    def run_cmd(self, command, env=None):
        return subprocess.run(
            f'cmd.exe /d /s /c "{command}"',
            cwd=self.temp.name, capture_output=True, input='\n',
            text=True, encoding='utf-8', errors='replace', timeout=30, env=env,
        )

    def test_double_click_entry_works_outside_package_with_unicode_and_spaces(self):
        result = self.run_cmd(f'"{self.package / "启动ACM.cmd"}" --help')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('--no-open', result.stdout)

    def test_command_preserves_user_path_and_runs_from_another_directory(self):
        reg = self.winreg
        original = r'%USERPROFILE%\original-tools;C:\keep this'
        with reg.CreateKey(reg.HKEY_CURRENT_USER, 'Environment') as key:
            reg.SetValueEx(key, 'Path', 0, reg.REG_EXPAND_SZ, original)
        self.launcher.install_windows_command(self.bin_dir)
        self.launcher.install_windows_command(self.bin_dir)
        value, kind = self.read_user_path()
        self.assertEqual(kind, reg.REG_EXPAND_SZ)
        self.assertEqual(value.split(';'), [*original.split(';'), str(self.bin_dir)])
        env = dict(os.environ, PATH=str(self.bin_dir) + os.pathsep + os.environ['PATH'])
        result = self.run_cmd('acm --help', env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('--no-open', result.stdout)

    def test_install_does_not_replace_an_existing_command_or_path(self):
        self.bin_dir.mkdir()
        target = self.bin_dir / 'acm.cmd'
        target.write_text('existing command', encoding='utf-8')
        before = self.read_user_path() if self.original_path else None
        with self.assertRaises(RuntimeError):
            self.launcher.install_windows_command(self.bin_dir)
        self.assertEqual(target.read_text(encoding='utf-8'), 'existing command')
        self.assertEqual(self.read_user_path() if self.original_path else None, before)


if __name__ == '__main__':
    unittest.main()

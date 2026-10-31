#!/usr/bin/env python3
"""ACM 练习台：后台启动、复用现有服务并打开浏览器。"""
import argparse
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import webbrowser


ROOT = Path(__file__).resolve().parent
TITLE = '<title>ACM 练习台 · Python</title>'.encode('utf-8')
# 只监听回环地址，不需要主机名。部分 macOS 的反向解析会让 http.server
# 在 bind 与 listen 之间卡住约 35 秒：actions/runner-images#14409。
SERVER_BOOTSTRAP = (
    "import socket, runpy; socket.getfqdn = lambda name='': name; "
    "runpy.run_module('http.server', run_name='__main__')"
)


def service_state(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        if sock.connect_ex(('127.0.0.1', port)) != 0:
            return 'stopped'
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f'http://127.0.0.1:{port}/', timeout=2) as response:
            if TITLE in response.read(65536):
                return 'ready'
    except OSError:
        pass
    return 'occupied'


def ensure_server(root, port=8765):
    url = f'http://127.0.0.1:{port}/'
    # Windows 的临时目录属于当前用户；POSIX 临时目录需要额外区分 uid。
    user = os.getuid() if os.name != 'nt' else 'windows'
    lock_path = Path(tempfile.gettempdir()) / f'acm-{user}-{port}.lock'
    with lock_path.open('a+b') as lock:
        if os.name == 'nt':
            import msvcrt
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        state = service_state(port)
        if state == 'ready':
            return url, None
        if state == 'occupied':
            raise RuntimeError(f'端口 {port} 被其他服务占用，未停止或修改该服务。')
        if not (root / 'index.html').is_file():
            raise RuntimeError(f'找不到网站文件：{root / "index.html"}。请保留整个启动包。')
        fd, log_name = tempfile.mkstemp(prefix='acm-practice-', suffix='.log')
        if os.name == 'nt':
            background = {'creationflags': subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            background = {'start_new_session': True}
        with os.fdopen(fd, 'ab', buffering=0) as log:
            process = subprocess.Popen(
                [sys.executable, '-u', '-c', SERVER_BOOTSTRAP, str(port),
                 '--bind', '127.0.0.1', '--directory', str(root)],
                cwd=root, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, **background,
            )
        for _ in range(50):
            if process.poll() is not None:
                break
            if service_state(port) == 'ready':
                return url, process
            time.sleep(.1)
        if process.poll() is None:
            process.terminate()
        process.wait()
        raise RuntimeError(f'服务启动失败，请查看日志：{log_name}')


def install_command(home=None):
    if os.name == 'nt':
        install_windows_command()
        return
    home = Path.home() if home is None else home
    target = home / '.local/bin/acm'
    script = Path(__file__).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if not target.is_symlink() or target.resolve() != script:
            raise RuntimeError(f'{target} 已存在，未覆盖。请先检查原命令。')
    else:
        script.chmod(script.stat().st_mode | 0o111)
        target.symlink_to(script)
    line = 'export PATH="$HOME/.local/bin:$PATH"'
    # Bash 只读取首个存在的登录配置；不要新建文件遮住原配置。
    bash_login = next((name for name in ('.bash_profile', '.bash_login', '.profile')
                       if (home / name).exists()), '.bash_profile')
    for name in ('.zshrc', '.bashrc', bash_login):
        config = home / name
        content = config.read_text() if config.exists() else ''
        if line not in content:
            with config.open('a') as file:
                file.write('\n# ACM 练习台快捷命令\n' + line + '\n')
    print('已安装 acm。新开一个终端，输入 acm 即可启动。')


def install_windows_command(bin_dir=None):
    import ctypes
    from ctypes import wintypes
    import winreg

    if bin_dir is None:
        local = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
        bin_dir = local / 'ACMPocket/bin'
    bin_dir = Path(bin_dir).resolve()
    target = bin_dir / 'acm.cmd'
    existing = shutil.which('acm')
    if existing and Path(existing).resolve() != target:
        raise RuntimeError(f'命令 acm 已被 {existing} 使用，未修改原命令或 PATH。可以继续双击启动ACM.cmd。')
    # 批处理文件内的百分号需转义；禁用延迟展开以支持路径中的感叹号。
    python = str(Path(sys.executable).resolve()).replace('%', '%%')
    script = str(Path(__file__).resolve()).replace('%', '%%')
    content = (
        '@echo off\r\nsetlocal DisableDelayedExpansion\r\nchcp 65001 >nul\r\n'
        f'"{python}" -X utf8 "{script}" %*\r\nexit /b %errorlevel%\r\n'
    ).encode('utf-8')
    if target.exists() and target.read_bytes() != content:
        raise RuntimeError(f'{target} 已存在，未覆盖。请先检查原命令。')
    # 只更新当前用户 PATH，保留原内容及 REG_EXPAND_SZ 中的环境变量。
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, 'Environment') as key:
        try:
            old_path, kind = winreg.QueryValueEx(key, 'Path')
        except FileNotFoundError:
            old_path, kind = '', winreg.REG_EXPAND_SZ
        entries = [os.path.normcase(os.path.normpath(os.path.expandvars(p.strip('"'))))
                   for p in old_path.split(';') if p]
        bin_dir.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        if os.path.normcase(str(bin_dir)) not in entries:
            new_path = old_path + ('' if not old_path or old_path.endswith(';') else ';') + str(bin_dir)
            winreg.SetValueEx(key, 'Path', 0, kind, new_path)
    # 通知资源管理器，让从开始菜单新打开的终端读取新 PATH。
    send = ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
                     wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
    send.restype = wintypes.LPARAM
    message = ctypes.create_unicode_buffer('Environment')
    result = ctypes.c_size_t()
    send(0xffff, 0x1a, 0, ctypes.addressof(message), 0x2, 2000, ctypes.byref(result))
    print('已安装 acm。请完全退出 Windows Terminal / PowerShell / CMD，重新打开后输入 acm。')


def main():
    parser = argparse.ArgumentParser(description='ACM 练习台：输入 acm，启动服务并打开网页。')
    parser.add_argument('--install', action='store_true', help='安装全局 acm 命令（当前用户）')
    parser.add_argument('--no-open', action='store_true', help='只启动服务，不打开浏览器')
    args = parser.parse_args()
    try:
        if args.install:
            install_command()
            return 0
        url, process = ensure_server(ROOT)
        print(('已在后台启动' if process else '练习台已在运行') + '：' + url)
        if not args.no_open:
            if not webbrowser.open(url):
                print('浏览器未自动打开，请手动访问上面的地址。')
        print('可以关闭这个终端。重启电脑后，再输入 acm 即可。')
        return 0
    except (OSError, RuntimeError) as error:
        print(f'启动失败：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

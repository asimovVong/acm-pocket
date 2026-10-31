#!/usr/bin/env python3
"""ACM 练习台：后台启动、复用现有服务并打开浏览器（macOS）。"""
import argparse
import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request


ROOT = Path(__file__).resolve().parent
TITLE = '<title>ACM 练习台 · Python</title>'.encode('utf-8')


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
    lock_path = Path(tempfile.gettempdir()) / f'acm-{os.getuid()}-{port}.lock'
    with lock_path.open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = service_state(port)
        if state == 'ready':
            return url, None
        if state == 'occupied':
            raise RuntimeError(f'端口 {port} 被其他服务占用，未停止或修改该服务。')
        if not (root / 'index.html').is_file():
            raise RuntimeError(f'找不到网站文件：{root / "index.html"}。请保留整个启动包。')
        fd, log_name = tempfile.mkstemp(prefix='acm-practice-', suffix='.log')
        with os.fdopen(fd, 'ab', buffering=0) as log:
            process = subprocess.Popen(
                [sys.executable, '-u', '-m', 'http.server', str(port),
                 '--bind', '127.0.0.1', '--directory', str(root)],
                cwd=root, stdin=subprocess.DEVNULL, stdout=log,
                stderr=subprocess.STDOUT, start_new_session=True,
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
            result = subprocess.run(['open', url], check=False)
            if result.returncode:
                print('浏览器未自动打开，请手动访问上面的地址。')
        print('可以关闭这个终端。重启电脑后，再输入 acm 即可。')
        return 0
    except (OSError, RuntimeError) as error:
        print(f'启动失败：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

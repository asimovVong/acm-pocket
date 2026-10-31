#!/bin/zsh
cd -- "${0:A:h}" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  print '需要 Python 3。请先从 python.org 安装 Python 3，再双击本文件。'
  read '?按回车关闭…'
  exit 1
fi
python3 ./launcher.py --install
result=$?
read '?按回车关闭…'
exit "$result"

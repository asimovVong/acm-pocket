# 公司笔试刷题手册

按「公司 / 笔试日期 / 题目」积累的个人 Python ACM 题库。本次收录微信中《滴滴9月6日机考笔试真题与解析》的两道题，题目、约束与六组原文样例于 2026-09-19 在微信内逐段核对。

- [层板限差：原始完整题目](companies/didi/2026-09-06/01-层板限差/原题.md)｜[完整讲解](companies/didi/2026-09-06/01-层板限差/讲解.md)｜[Python 程序](companies/didi/2026-09-06/01-层板限差/solution.py)
- [管材四切：原始完整题目](companies/didi/2026-09-06/02-管材四切/原题.md)｜[完整讲解](companies/didi/2026-09-06/02-管材四切/讲解.md)｜[Python 程序](companies/didi/2026-09-06/02-管材四切/solution.py)
- [来源核对记录](companies/didi/2026-09-06/来源与场次.md)
- [验证记录](VERIFICATION.md)

## 打开网站

在本地服务器运行期间，访问 <http://127.0.0.1:8765/company-exams/>。基础算法练习台侧栏也提供入口。

服务器未运行时：

```bash
# 在项目根目录执行
python3 -m http.server 8765 --bind 127.0.0.1
```

无需安装新依赖。网站复用上一层的 worker.js 和 runner.py，Python 在浏览器 Worker 中执行。首次进入练习页需要联网加载现有的 Pyodide 314.0.7；题面、讲解与演示不需要 Python 就绪。直接双击 index.html 受浏览器本地文件限制，请使用上述网站地址。

## 建议学习顺序

1. 先读每题「原始完整题目」，再依次读「题意解释」「输入解释」「输出解释」「范围解释」。原题保留原变量、约束和每组样例的输入、输出、说明。
2. 在「动手看过程」中操作指针或切口，观察答案如何变化。
3. 回到推导，读清楚为什么可以相乘、为什么可以分别均分。
4. 打开「Python 练习」，在已写好读入的模板里补算法。
5. 用原文样例和补充边界验证；需要时展开完整参考解法。
6. 确认自己能独立写出，再手动标记已完成。

参考运行、验证、复制与下载不会替换练习草稿。草稿、输入和进度使用单独的 localStorage 键 company-exams-v1，按题保存；不会访问旧练习台的草稿。换浏览器或清理站点数据会影响本地保存，重要代码请下载。保存失败时页面会提示下载。运行结果在代码或输入改动后失效。

每组最长执行 3 秒，标准输出上限 64 KiB；超时可重新加载运行环境。浏览器用例按空白分隔比较，只适用于本次两道单整数输出题。补充用例与本地穷举不代表官方隐藏评测。

## 文件目录

```text
company-exams/
├── README.md
├── VERIFICATION.md
├── index.html / styles.css / app.js   网站
├── models.mjs                        小样例交互演示
├── build.py                          从文档、代码、用例生成网页题库
├── catalog.json                      生成结果
├── tests/                            穷举对照与演示测试
└── companies/
    └── didi/
        └── 2026-09-06/
            ├── 来源与场次.md
            ├── 01-层板限差/
            │   ├── 原题.md
            │   ├── 原题截图/              第一题用户提供的三张截图
            │   ├── 讲解.md
            │   ├── solution.py
            │   └── cases.json
            └── 02-管材四切/
                ├── 原题.md
                ├── 讲解.md
                ├── solution.py
                └── cases.json
```

本题库只收录本次请求中的这两道题。微信其他已打开标签页的题目尚未收录。

## 本地运行解法

```bash
python3 'companies/didi/2026-09-06/01-层板限差/solution.py' <<'EOF'
3 1
1 2 3
EOF

python3 'companies/didi/2026-09-06/02-管材四切/solution.py' <<'EOF'
5
4 5 1 2 8
EOF
```

分别输出 4 和 5。两题均为单组输入，无开头的测试组数 T。

## 更新和检查

在本目录运行：

```bash
python3 build.py
python3 tests/verify_solutions.py
node --test tests/models.test.mjs
```

原题以各目录中的原题.md 为准，build.py 会自动把完整原题同步进讲解.md 和网页，讲解部分独立维护。修改题面、代码或用例后重新生成 catalog.json，再刷新网页。文档内代码块与 solution.py 应同步修改。新增题目时，在 companies/公司/日期/题目 下新增文档、代码、用例，补充 build.py 的 specs 和导航分组。

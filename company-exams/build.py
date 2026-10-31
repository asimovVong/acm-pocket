"""Build the browser catalog from local Markdown, Python and cases; no dependencies."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parent
SESSION = ROOT / 'companies/didi/2026-09-06'


def inline(s):
    s = html.escape(s)
    # Preserve only the subscript tags used by transcribed mathematical notation.
    s = re.sub(r'&lt;(/?sub)&gt;', r'<\1>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\((https://[^)]+)\)', r'<a href="\2" target="_blank" rel="noreferrer">\1</a>', s)
    return s


def render(md):
    # Deliberately small renderer for the headings/lists/fences used in these notes.
    out, paragraph, fence, code, listing = [], [], False, [], None
    def flush():
        if paragraph:
            out.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()
    def close_list():
        nonlocal listing
        if listing:
            out.append(f'</{listing}>')
            listing = None
    for line in md.splitlines():
        if line.startswith('```'):
            flush(); close_list()
            if fence:
                out.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>')
                code = []
            fence = not fence
        elif fence:
            code.append(line)
        elif not line.strip():
            flush(); close_list()
        elif line.startswith('#'):
            flush(); close_list()
            level = len(line) - len(line.lstrip('#'))
            out.append(f'<h{level}>' + inline(line[level:].strip()) + f'</h{level}>')
        elif re.match(r'^(?:- |\d+\. )', line):
            flush()
            kind = 'ul' if line.startswith('- ') else 'ol'
            if listing != kind:
                close_list(); out.append(f'<{kind}>'); listing = kind
            out.append('<li>' + inline(re.sub(r'^(?:- |\d+\. )', '', line)) + '</li>')
        else:
            paragraph.append(line)
    flush(); close_list()
    return '\n'.join(out)


specs = [
    dict(id='didi-20260906-shelf', folder='01-层板限差', title='层板限差', number='01',
         topic='排序 + 双指针 + 计数', complexity='O(n log n)',
         summary='上面的箱子最多比下面矮 d。合法的摆放顺序，一共有多少种？',
         insight='先放高箱子，再给矮箱子数一数能插入的位置。',
         bounds='n ≤ 200000，高度 ≤ 1000000', demo='shelf',
         starter='import sys\n\nMOD = 998244353\n\ndef count_arrangements(heights, d):\n    # 先排序，再计算每个箱子有几个插入位置。\n    pass\n\ndef solve():\n    input = sys.stdin.readline\n    n, d = map(int, input().split())\n    heights = list(map(int, sys.stdin.read().split()))\n    print(count_arrangements(heights, d))\n\nif __name__ == "__main__":\n    solve()\n'),
    dict(id='didi-20260906-pipe', folder='02-管材四切', title='管材四切', number='02',
         topic='前缀和 + 双指针', complexity='O(n)',
         summary='把正整数数组切成四段，让最大段和与最小段和的差尽量小。',
         insight='固定中间一刀，再让左右两边各自切得更均匀。',
         bounds='n ≤ 100000，单项 ≤ 10⁹', demo='pipe',
         starter='import sys\n\ndef min_range(values):\n    # 前缀和 → 枚举中间切口 → 左右各找最均衡的切法。\n    pass\n\ndef solve():\n    input = sys.stdin.readline\n    n = int(input())\n    values = list(map(int, sys.stdin.read().split()))\n    print(min_range(values))\n\nif __name__ == "__main__":\n    solve()\n')
]
for item in specs:
    directory = SESSION / item['folder']
    item.update(company='滴滴', date='2026-09-06',
                source='https://mp.weixin.qq.com/s/lxkbH776rnz3PgnzkNKE4w',
                sourceTitle='滴滴9月6日机考笔试真题与解析',
                directory=directory.relative_to(ROOT).as_posix())
    md = (directory/'讲解.md').read_text()
    original = (directory/'原题.md').read_text().split('\n', 1)[1].strip()
    original = re.sub(r'^## ', '### ', original, flags=re.M)
    original_section = (
        '## 原始完整题目\n\n'
        '以下按微信原文转录，保留原变量 m、约束和全部样例；仅统一公式、空格与数字排版。'
        '来源：[滴滴9月6日机考笔试真题与解析](https://mp.weixin.qq.com/s/lxkbH776rnz3PgnzkNKE4w)。'
        '后面的题意、输入输出与范围解释为学习讲解。\n\n' + original + '\n'
    )
    md = re.sub(
        r'<!-- original:start -->.*?<!-- original:end -->',
        lambda _: '<!-- original:start -->\n' + original_section + '\n<!-- original:end -->',
        md, count=1, flags=re.S,
    )
    (directory/'讲解.md').write_text(md)
    # Browser reference code is shown independently from the learner's draft.
    body = md.split('<!-- original:end -->', 1)[1]
    body = re.sub(r'## 完整 Python 程序\n\n```python\n.*?```\n', '', body, flags=re.S)
    item['lesson'] = ('<section class="original-problem" aria-label="原始完整题目">'
                      + render(original_section) + '</section>\n' + render(body))
    item['reference'] = (directory/'solution.py').read_text()
    item['cases'] = json.loads((directory/'cases.json').read_text())
(ROOT/'catalog.json').write_text(json.dumps(specs, ensure_ascii=False, indent=2)+'\n')
print('Built 2 problems from Markdown, Python and sample files.')

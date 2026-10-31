# 题库数据约定

题源及章节以 source-manifest.json 为准。每个数据文件是 JSON array。字段：

```text
id: string，力扣题号，60 道去重
title: string，中文题名
topic: string，以下之一：双指针、滑动窗口、二分查找、链表、二叉树、回溯、动态规划、单调栈、单调队列
episode: number，首次出现的集号
episodes: number[]，重复出现时列出所有章节，例如 42 为 [2,26]
url: string，原题 URL
statement: string，自己撰写的简短准确题意，含关键前提，避免抄录长文本
inputFormat: string，换行分隔的明确 ACM 标准输入约定
outputFormat: string，明确标准输出格式
starter: string，可直接保存为 .py 的完整读入及结构辅助模板，算法部分留给用户；不要给出完整解法。模板必须语法有效，不依赖自定义第三方模块。
judge: "tokens" | "json" | "unordered" | "unordered-nested" | "peak"
cases: [{name:string, stdin:string, expected:string}]，至少 3 个手工可核验测试，其中含边界。209 保留 6 组。
```

输出约定：标量整数与布尔值用 tokens，布尔以 1/0 表示；数组、嵌套数组、字符串集合等输出用 `print(json.dumps(answer, ensure_ascii=False))`。

judge 含义：tokens 按空白 token 精确比较；json 按 JSON 值和结构比较；unordered 对最外层数组忽略顺序，保留子数组顺序；unordered-nested 最外层及每个直接子数组内部忽略顺序（组合/子集等），仍比较重复项；peak 对 162 从 stdin n 和数组中验证任意有效下标，其 expected 给一个合法示例。

输入优先普通 ACM 格式：数组先 n（若有 target/k 则同第一行），第二行数值。字符串用独立整行；二叉树用一行 JSON 层序数组，null 表示缺失结点；结构题可用 JSON 输入，但需要在说明和模板中完全一致。不要假装链表题只是普通数组题，提供 ListNode、建链和必要序列化辅助代码；不在辅助代码中包含所求算法。

所有数据为本地练习自编用例，不声称力扣完整评测。测试预期不得由模板或被测实现动态生成。

## 作者题解的 ACM 参考

与原题库独立的 `references-arrays.json`、`references-structures.json`、`references-dp.json` 各为 array：

```text
id: string，对应题号，每题恰好一份完整参考
author: "灵茶山艾府"
sourceUrl: string，实际核验的作者对应题解直链
sourceTitle: string，题解标题
variant: string，所选具体算法版本，中文
imports: [{code:string, purpose:string}]，完整参考中的全部 import 语句及其用途
code: string，可直接运行的 Python ACM 程序，包含算法和 I/O
note: string，说明依据作者解法适配，以及必要的差异或递归范围
verifiedAt: string，核验日期 YYYY-MM-DD
```

参考代码不写入个人 `drafts`，不会因查看或运行参考而替换草稿。作者文章有多种解法时，标明当前采用哪一种，不暗示导入项适用于其他所有版本。

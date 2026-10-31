# 许可证范围与第三方来源

## 本项目的原创代码

ACM Pocket 的原创练习台代码、判题与运行适配器、启动器、测试以及原创文档采用根目录的 [MIT 许可证](LICENSE)，版权声明为 `Copyright (c) 2026 asimovVong`。

本许可仅授予项目维护者有权授予的权利。下述第三方题目、题解、截图和运行时不因收录在本仓库而被重新授予 MIT 许可；文件中同时包含原创与第三方内容时，这一区分同样适用。

## 灵茶山艾府的课程与题解

- 作者：[灵茶山艾府（endlesscheng）](https://leetcode.cn/u/endlesscheng/)。
- 视频课程：[B 站《基础算法精讲》](https://space.bilibili.com/206214/channel/collectiondetail?sid=842776)。
- 最初跟学入口：[相向双指针（二）](https://www.bilibili.com/video/BV1Qg411q7ia/)。
- 配套题单：[EndlessCheng/codeforces-go 的基础算法精讲题目汇总](https://github.com/EndlessCheng/codeforces-go/blob/master/leetcode/README.md)。

`data/references-arrays.json`、`data/references-structures.json`、`data/references-dp.json` 中的每条参考均保留 `author`、`sourceUrl`、`variant` 和 `note`，说明对应作者文章、所选解法与 ACM 适配。原题解及其改编部分保留原作者权利，不包含在本项目原创代码的 MIT 授权中。再次使用时应保留署名和来源，并核对相应来源的许可；需要额外授权的用途须向权利人取得授权。

原作者 GitHub 仓库的 [MIT 许可证](https://github.com/EndlessCheng/codeforces-go/blob/master/LICENSE) 适用于该仓库授权的材料；本项目不据此将其力扣文章、B 站视频或其他平台内容一并认定为 MIT。

## 力扣题目与题库数据

`data/arrays.json`、`data/structures.json`、`data/dp.json` 以及 `data/source-manifest.json` 对应的题目来自 LeetCode / 力扣。题目相关的第三方表达及原始样例保留相应权利人的权利。各题记录提供原题链接。

本项目整理的练习输入输出约定、程序适配和自编用例不代表力扣官方测试或官方 ACM 格式。题目和题解的收录不代表原作者或平台参与开发、授权背书。

## 公司笔试学习资料

`company-exams/companies/didi/2026-09-06/` 下的原始题面、原文样例、截图，以及其在 `讲解.md` 和 `company-exams/catalog.json` 中的副本，来自微信公众号「塔子哥学算法」的[《滴滴9月6日机考笔试真题与解析》](https://mp.weixin.qq.com/s/lxkbH776rnz3PgnzkNKE4w)。这些第三方内容不在本项目 MIT 授权范围内。

详细来源和独立整理范围见[来源与场次](company-exams/companies/didi/2026-09-06/来源与场次.md)。公司及场次归属来自第三方文章，未独立确认为公司官方发布。

## 浏览器 Python 运行时

网站通过 CDN 加载 [Pyodide](https://github.com/pyodide/pyodide)，当前启动包不捆绑其运行时。Pyodide、Python 及其运行时组件分别适用上游[许可证与第三方许可说明](https://github.com/pyodide/pyodide/blob/main/LICENSE)，不适用本项目的 MIT 许可证。

如后续自行打包离线运行时，应保留对应版本随附的许可证和版权声明。
